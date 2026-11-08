import json
import re
from datetime import date as date_cls
from functools import wraps

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

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
                "bookId": r.book_id,
                "active": r.book.is_active,
                "title": r.book.title,
                "author": r.book.author.name,
                "pages": r.book.pages,
                "current": r.current_page,
                "status": r.status,
                "genre": r.book.genre,
                "startedAt": r.started_at.isoformat() if r.started_at else None,
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


def api_get_view(func):
    """GET + login talab qiladi (qidiruv uchun)."""

    @wraps(func)
    @require_GET
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return error("auth", status=401)
        return func(request, *args, **kwargs)

    return wrapper


def error(code, status=400, **params):
    return JsonResponse({"error": code, "params": params}, status=status)


def ok(request, notice=None):
    data = {"state": build_state(request.user)}
    if notice:
        data["notice"] = notice
    return JsonResponse(data)


# O'zbek lotin yozuvida apostrof turlicha yoziladi: o' o` oʻ o‘ o’ — hammasi bir xil.
APOSTROPHES = "'`ʻʼ‘’"
APOSTROPHE_CLASS = "[" + re.escape(APOSTROPHES) + "]"


def clean_text(value, limit):
    return " ".join(str(value or "").split())[:limit]


def name_regex(text, exact=False):
    """Katta-kichik harf, apostrof turi va bo'shliqlarga befarq qidiruv regex'i."""
    parts = []
    for ch in text:
        if ch in APOSTROPHES:
            parts.append(APOSTROPHE_CLASS)
        elif ch.isspace():
            parts.append(r"\s+")
        else:
            parts.append(re.escape(ch))
    pattern = "".join(parts)
    return f"^{pattern}$" if exact else pattern


def visible_to(user):
    """Tasdiqlangan yozuvlar + foydalanuvchining o'zi qo'shgan (tekshiruvdagi) yozuvlar."""
    return Q(is_active=True) | Q(created_by=user)


def rank(name, query):
    name = name.lower()
    query = query.lower()
    return (0 if name.startswith(query) else 1, name)


def to_int(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


@api_get_view
def search_books(request):
    query = clean_text(request.GET.get("q"), 100)
    if not query:
        return JsonResponse({"results": []})
    rx = name_regex(query)
    books = list(
        Book.objects.filter(visible_to(request.user))
        .filter(Q(title__iregex=rx) | Q(author__name__iregex=rx))
        .select_related("author")[:30]
    )
    books.sort(key=lambda b: (not b.is_active, *rank(b.title, query)))
    books = books[:8]
    in_list = set(
        Reading.objects.filter(user=request.user, book_id__in=[b.id for b in books]).values_list("book_id", flat=True)
    )
    return JsonResponse({"results": [
        {
            "id": b.id,
            "title": b.title,
            "author": b.author.name,
            "pages": b.pages,
            "genre": b.genre,
            "active": b.is_active,
            "inList": b.id in in_list,
        }
        for b in books
    ]})


@api_get_view
def search_authors(request):
    query = clean_text(request.GET.get("q"), 100)
    if not query:
        return JsonResponse({"results": []})
    authors = list(
        Author.objects.filter(visible_to(request.user)).filter(name__iregex=name_regex(query))[:30]
    )
    authors.sort(key=lambda a: (not a.is_active, *rank(a.name, query)))
    return JsonResponse({"results": [
        {"id": a.id, "name": a.name, "active": a.is_active} for a in authors[:8]
    ]})


@api_view
def add_book(request, data):
    """Kitobni kitobxon ro'yxatiga qo'shadi.

    Ikki yo'l bor:
    * `bookId` — katalogdan tanlangan kitob;
    * `title` + `author`/`authorId` + `pages` + `genre` — katalogda yo'q yangi kitob.
      U tasdiqlanmagan holatda yaratiladi (admin tasdiqlaguncha faqat shu kitobxonga ko'rinadi).
    """
    user = request.user
    started = data.get("status", "reading") != "want"
    notice = "added"

    if data.get("bookId") not in (None, ""):
        book = Book.objects.filter(visible_to(user), pk=to_int(data.get("bookId"))).first()
        if book is None:
            return error("not_found", status=404)
    else:
        title = clean_text(data.get("title"), 301)
        author_name = clean_text(data.get("author"), 201)
        pages = to_int(data.get("pages"))
        genre = data.get("genre")

        if not title:
            return error("title_required")
        if len(title) > 300:
            return error("title_too_long")

        author = None
        if data.get("authorId") not in (None, ""):
            author = Author.objects.filter(visible_to(user), pk=to_int(data.get("authorId"))).first()
            if author is None:
                return error("not_found", status=404)
        elif not author_name:
            return error("author_required")
        elif len(author_name) > 200:
            return error("author_too_long")

        if author is None:
            # Bir xil nomli muallif (tekshiruvdagisi ham) bo'lsa — o'shani ishlatamiz, dublikat qilmaymiz.
            author = Author.objects.filter(name__iregex=name_regex(author_name, exact=True)).first()

        book = None
        if author is not None:
            book = Book.objects.filter(author=author, title__iregex=name_regex(title, exact=True)).first()

        if book is None:
            if pages is None or not 1 <= pages <= MAX_BOOK_PAGES:
                return error("pages_invalid", max=MAX_BOOK_PAGES)
            if genre not in Book.Genre.values:
                genre = Book.Genre.OTHER
            try:
                with transaction.atomic():
                    if author is None:
                        author = Author.objects.create(name=author_name, created_by=user)
                    book = Book.objects.create(
                        title=title, author=author, pages=pages, genre=genre, created_by=user
                    )
            except IntegrityError:
                return error("book_exists")
        if not book.is_active:
            notice = "pending"

    reading, created = Reading.objects.get_or_create(user=user, book=book)
    if not created:
        return error("book_exists")
    if started:
        reading.started_at = timezone.localdate()
        reading.save(update_fields=["started_at"])
        reading.recalculate()
    return ok(request, notice)


@api_view
def start_reading(request, data, pk):
    reading = Reading.objects.select_related("book").filter(pk=pk, user=request.user).first()
    if reading is None:
        return error("not_found", status=404)
    if reading.started_at is None:
        reading.started_at = timezone.localdate()
        reading.save(update_fields=["started_at"])
        reading.recalculate()
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
