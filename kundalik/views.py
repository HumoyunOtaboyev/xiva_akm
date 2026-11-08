import json
from datetime import date as date_cls
from functools import wraps

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import EmailAuthenticationForm, RegisterForm
from .models import MAX_BOOK_PAGES, Author, Book, Reading, ReadingLog


# ---------------------------------------------------------------- auth

class KundalikLoginView(LoginView):
    template_name = "kundalik/login.html"
    authentication_form = EmailAuthenticationForm
    redirect_authenticated_user = True


def register(request):
    if request.user.is_authenticated:
        return redirect("kundalik:dashboard")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        return redirect("kundalik:dashboard")
    return render(request, "kundalik/register.html", {"form": form})


# ---------------------------------------------------------------- state

def build_state(user):
    """Dashboard uchun foydalanuvchining barcha ma'lumotlari (JSON)."""
    readings = list(
        Reading.objects.filter(user=user).select_related("book__author").order_by("-created_at", "-id")
    )
    logs = list(
        ReadingLog.objects.filter(reading__user=user)
        .select_related("reading__book")
        .order_by("date", "id")
    )

    # Har bir yozuv uchun — o'sha yozuvdan keyingi progress (joriy emas).
    cumulative = {}
    log_items = []
    for log in logs:
        total = cumulative.get(log.reading_id, 0) + log.pages
        cumulative[log.reading_id] = total
        pages = log.reading.book.pages
        log_items.append({
            "id": log.id,
            "readingId": log.reading_id,
            "date": log.date.isoformat(),
            "pages": log.pages,
            "note": log.note,
            "progress": min(100, round(total * 100 / pages)) if pages else 0,
        })
    log_items.reverse()  # eng yangisi birinchi

    return {
        "today": timezone.localdate().isoformat(),
        "books": [
            {
                "id": r.id,
                "title": r.book.title,
                "author": r.book.author.name,
                "pages": r.book.pages,
                "current": r.current_page,
                "status": r.status,
                "genre": r.book.genre,
                "finishedAt": r.finished_at.isoformat() if r.finished_at else None,
            }
            for r in readings
        ],
        "logs": log_items,
    }


@login_required
def dashboard(request):
    user = request.user
    return render(request, "kundalik/dashboard.html", {
        "state": build_state(user),
        "genres": Book.Genre.choices,
        "display_name": user.get_full_name() or user.username,
    })


# ---------------------------------------------------------------- JSON API

def api_view(func):
    """POST + login talab qiladi, JSON body ni `data` sifatida uzatadi."""

    @wraps(func)
    @require_POST
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return error("auth", status=401)
        try:
            data = json.loads(request.body or b"{}")
        except (ValueError, UnicodeDecodeError):
            return error("bad_request")
        if not isinstance(data, dict):
            return error("bad_request")
        return func(request, data, *args, **kwargs)

    return wrapper


def error(code, status=400, **params):
    return JsonResponse({"error": code, "params": params}, status=status)


def ok(request):
    return JsonResponse({"state": build_state(request.user)})


def to_int(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


@api_view
def add_book(request, data):
    title = str(data.get("title") or "").strip()
    author_name = " ".join(str(data.get("author") or "").split())
    pages = to_int(data.get("pages"))
    genre = data.get("genre")

    if not title:
        return error("title_required")
    if len(title) > 300:
        return error("title_too_long")
    if not author_name:
        return error("author_required")
    if len(author_name) > 200:
        return error("author_too_long")
    if pages is None or not 1 <= pages <= MAX_BOOK_PAGES:
        return error("pages_invalid", max=MAX_BOOK_PAGES)
    if genre not in Book.Genre.values:
        genre = Book.Genre.OTHER

    try:
        with transaction.atomic():
            author = Author.objects.filter(name__iexact=author_name).first()
            if author is None:
                author = Author.objects.create(name=author_name)
            book = Book.objects.filter(title__iexact=title, author=author).first()
            if book is None:
                book = Book.objects.create(
                    title=title, author=author, pages=pages, genre=genre, created_by=request.user
                )
            _, created = Reading.objects.get_or_create(user=request.user, book=book)
    except IntegrityError:
        return error("book_exists")
    if not created:
        return error("book_exists")
    return ok(request)


@api_view
def delete_book(request, data, pk):
    reading = Reading.objects.filter(pk=pk, user=request.user).first()
    if reading is None:
        return error("not_found", status=404)
    reading.delete()
    return ok(request)


@api_view
def add_log(request, data):
    reading = (
        Reading.objects.select_related("book")
        .filter(pk=to_int(data.get("bookId")), user=request.user)
        .first()
    )
    if reading is None:
        return error("book_required")

    today = timezone.localdate()
    raw_date = str(data.get("date") or "").strip()
    try:
        log_date = date_cls.fromisoformat(raw_date) if raw_date else today
    except ValueError:
        return error("date_invalid")
    if log_date > today:
        return error("date_future")

    pages = to_int(data.get("pages"))
    if pages is None or pages < 1:
        return error("pages_invalid", max=MAX_BOOK_PAGES)

    remaining = reading.book.pages - reading.current_page
    if remaining <= 0:
        return error("already_completed")
    if pages > remaining:
        return error("pages_exceed", max=remaining)

    note = str(data.get("note") or "").strip()[:300]
    ReadingLog.objects.create(reading=reading, date=log_date, pages=pages, note=note)
    return ok(request)


@api_view
def delete_log(request, data, pk):
    log = ReadingLog.objects.select_related("reading__book").filter(pk=pk, reading__user=request.user).first()
    if log is None:
        return error("not_found", status=404)
    log.delete()
    return ok(request)
