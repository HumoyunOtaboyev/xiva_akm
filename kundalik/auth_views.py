"""Saytning umumiy kirish tizimi: kirish, ro'yxatdan o'tish (email kod bilan), parolni tiklash.

URL'lar sayt ildizida (`/kirish/`, `/royxatdan-otish/`, ...) — `kundalik/auth_urls.py`.
O'qish kundaligi kabi yopiq sahifalar kirmagan foydalanuvchini shu yerga `?next=` bilan yuboradi;
kirish yoki ro'yxatdan o'tish tugagach foydalanuvchi o'sha sahifaga qaytadi.
"""

from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from .emails import mask_email, send_code
from .forms import (
    EmailAuthenticationForm,
    PasswordResetConfirmForm,
    PasswordResetRequestForm,
    RegisterForm,
    VerifyCodeForm,
)
from .models import EmailCode, EmailVerification, PasswordResetCode

User = get_user_model()

PENDING_SESSION_KEY = "kundalik_pending_user"
RESET_SESSION_KEY = "kundalik_reset_email"
NEXT_SESSION_KEY = "accounts_next"
CODE_ERRORS = {
    "invalid": "Kod noto'g'ri. Yana {left} ta urinish qoldi.",
    "expired": "Kodning muddati tugagan. «Kodni qayta yuborish» tugmasini bosing.",
    "too_many": "Urinishlar soni tugadi. «Kodni qayta yuborish» tugmasini bosing.",
}
SEND_FAILED = (
    "Kodni emailga yuborib bo'lmadi. Birozdan keyin «Kodni qayta yuborish» tugmasini bosing "
    "yoki markaz bilan bog'laning."
)
BACKEND = "django.contrib.auth.backends.ModelBackend"


# ---------------------------------------------------------------- next (qaytish manzili)

def safe_next(request, value):
    if value and url_has_allowed_host_and_scheme(
        value, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return value
    return ""


def remember_next(request):
    """So'rovdagi `next` ni sessiyaga saqlaydi (ro'yxatdan o'tish / parol tiklash bir necha qadamli)."""
    nxt = safe_next(request, request.POST.get("next") or request.GET.get("next"))
    if nxt:
        request.session[NEXT_SESSION_KEY] = nxt
    return nxt


def next_context(request):
    nxt = safe_next(request, request.POST.get("next") or request.GET.get("next")) or request.session.get(
        NEXT_SESSION_KEY, ""
    )
    return {"next": nxt, "for_kundalik": nxt.startswith("/kundalik")}


def finish_login(request, user):
    """Foydalanuvchini kiritadi va saqlangan `next` (yoki bosh sahifa)ga yo'naltiradi."""
    nxt = request.session.pop(NEXT_SESSION_KEY, "")
    login(request, user, backend=BACKEND)
    return redirect(safe_next(request, nxt) or "home")


# ---------------------------------------------------------------- kirish

def send_new_code(request, user):
    """Yangi kod yaratib yuboradi va foydalanuvchini sessiyada "kutilmoqda" deb belgilaydi."""
    _, code = EmailVerification.issue(user)
    request.session[PENDING_SESSION_KEY] = user.pk
    if not send_code(user, code, "verify"):
        messages.error(request, SEND_FAILED)
        return False
    return True


class SiteLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = EmailAuthenticationForm
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["for_kundalik"] = (context.get("next") or "").startswith("/kundalik")
        return context

    def form_valid(self, form):
        user = form.pending_user
        if user is None:
            self.request.session.pop(NEXT_SESSION_KEY, None)
            return super().form_valid(form)
        # Parol to'g'ri, lekin email hali tasdiqlanmagan.
        remember_next(self.request)
        verification = EmailVerification.objects.get(user=user)
        if verification.can_resend():
            if send_new_code(self.request, user):
                messages.info(self.request, "Emailingiz hali tasdiqlanmagan. Yangi kod yubordik.")
        else:
            self.request.session[PENDING_SESSION_KEY] = user.pk
            messages.info(self.request, "Emailingiz hali tasdiqlanmagan. Emailga yuborilgan kodni kiriting.")
        return redirect("accounts:verify")


class SiteLogoutView(LogoutView):
    next_page = "home"


def register(request):
    if request.user.is_authenticated:
        return redirect(safe_next(request, request.GET.get("next")) or "home")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        remember_next(request)
        user = form.save()
        send_new_code(request, user)
        return redirect("accounts:verify")
    return render(request, "accounts/register.html", {"form": form, **next_context(request)})


def verify_email(request):
    """Emailga yuborilgan 6 xonali kodni tekshiradi; to'g'ri bo'lsa hisobni faollashtirib kiritadi."""
    user_id = request.session.get(PENDING_SESSION_KEY)
    user = User.objects.filter(pk=user_id, is_active=False).first() if user_id else None
    verification = EmailVerification.objects.filter(user=user).first() if user else None
    if verification is None:
        request.session.pop(PENDING_SESSION_KEY, None)
        return redirect("home" if request.user.is_authenticated else "accounts:register")

    form = VerifyCodeForm()
    if request.method == "POST":
        if "resend" in request.POST:
            wait = verification.seconds_until_resend()
            if wait:
                messages.error(request, f"Yangi kodni {wait} soniyadan keyin so'rashingiz mumkin.")
            elif send_new_code(request, user):
                messages.success(request, "Yangi kod yuborildi. Avvalgi kod endi ishlamaydi.")
            return redirect("accounts:verify")

        form = VerifyCodeForm(request.POST)
        if form.is_valid():
            result = verification.check_code(form.cleaned_data["code"])
            if result == "ok":
                user.is_active = True
                user.save(update_fields=["is_active"])
                verification.delete()
                request.session.pop(PENDING_SESSION_KEY, None)
                return finish_login(request, user)
            form.add_error("code", CODE_ERRORS[result].format(left=verification.attempts_left))

    return render(request, "accounts/verify.html", {
        "form": form,
        "masked_email": mask_email(user.email),
        "minutes": int(EmailCode.CODE_TTL.total_seconds() // 60),
        "resend_wait": verification.seconds_until_resend(),
    })


# ---------------------------------------------------------------- parolni tiklash

def reset_user_for(email):
    """Parolni tiklash mumkin bo'lgan foydalanuvchi: faol yoki emailini tasdiqlamagan.

    Admin bloklagan (faol emas va tasdiqlash kutilmayotgan) hisoblar uchun None.
    """
    user = User.objects.filter(username__iexact=email).first() if email else None
    if user is None or not (user.is_active or EmailVerification.is_pending(user)):
        return None
    return user


def send_reset_code(user):
    _, code = PasswordResetCode.issue(user)
    return send_code(user, code, "reset")


def password_reset_request(request):
    """1-qadam: email kiritiladi. Email ro'yxatda bor-yo'qligi oshkor qilinmaydi."""
    form = PasswordResetRequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        remember_next(request)
        email = form.cleaned_data["email"]
        user = reset_user_for(email)
        if user is not None:
            record = PasswordResetCode.objects.filter(user=user).first()
            if (record is None or record.can_resend()) and not send_reset_code(user):
                messages.error(request, SEND_FAILED)
        request.session[RESET_SESSION_KEY] = email
        return redirect("accounts:password_reset_confirm")
    return render(request, "accounts/password_reset.html", {"form": form, **next_context(request)})


def password_reset_confirm(request):
    """2-qadam: kod + yangi parol. To'g'ri bo'lsa parol almashadi va foydalanuvchi tizimga kiradi."""
    email = request.session.get(RESET_SESSION_KEY)
    if not email:
        return redirect("accounts:password_reset")
    user = reset_user_for(email)
    record = PasswordResetCode.objects.filter(user=user).first() if user else None

    form = PasswordResetConfirmForm(user=user)
    if request.method == "POST":
        if "resend" in request.POST:
            wait = record.seconds_until_resend() if record else 0
            if wait:
                messages.error(request, f"Yangi kodni {wait} soniyadan keyin so'rashingiz mumkin.")
            elif user is None or send_reset_code(user):
                # Email ro'yxatda bo'lmasa ham bir xil javob.
                messages.success(request, "Yangi kod yuborildi. Avvalgi kod endi ishlamaydi.")
            else:
                messages.error(request, SEND_FAILED)
            return redirect("accounts:password_reset_confirm")

        form = PasswordResetConfirmForm(request.POST, user=user)
        if form.is_valid():
            result = record.check_code(form.cleaned_data["code"]) if record else "invalid"
            if result == "ok":
                user.set_password(form.cleaned_data["new_password1"])
                # Kod emailga keldi — demak email ham tasdiqlangan.
                user.is_active = True
                user.save(update_fields=["password", "is_active"])
                EmailVerification.objects.filter(user=user).delete()
                record.delete()
                request.session.pop(RESET_SESSION_KEY, None)
                request.session.pop(PENDING_SESSION_KEY, None)
                return finish_login(request, user)
            left = record.attempts_left if record else EmailCode.MAX_ATTEMPTS
            form.add_error("code", CODE_ERRORS[result].format(left=left))

    return render(request, "accounts/password_reset_confirm.html", {
        "form": form,
        "masked_email": mask_email(email),
        "minutes": int(EmailCode.CODE_TTL.total_seconds() // 60),
        "resend_wait": record.seconds_until_resend() if record else 0,
    })
