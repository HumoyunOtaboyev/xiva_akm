import logging

from django.core.mail import send_mail
from django.template.loader import render_to_string

from .models import EmailCode

logger = logging.getLogger(__name__)

PURPOSES = {
    "verify": {
        "subject": "{code} — Xiva shahar AKM tasdiqlash kodi",
        "intro": "«O'qish kundaligi»da ro'yxatdan o'tishni yakunlash uchun quyidagi kodni kiriting:",
        "ignore_note": "Agar siz ro'yxatdan o'tmagan bo'lsangiz, bu xatga e'tibor bermang.",
    },
    "reset": {
        "subject": "{code} — Xiva shahar AKM parolni tiklash kodi",
        "intro": "«O'qish kundaligi» parolini tiklash uchun quyidagi kodni kiriting:",
        "ignore_note": "Agar parolni tiklashni siz so'ramagan bo'lsangiz, bu xatga e'tibor bermang — parolingiz o'zgarmaydi.",
    },
}


def send_code(user, code, purpose):
    """Kodni emailga yuboradi. Xatolik bo'lsa False qaytaradi (va logga yozadi)."""
    texts = PURPOSES[purpose]
    context = {
        "name": user.first_name or user.email,
        "code": code,
        "minutes": int(EmailCode.CODE_TTL.total_seconds() // 60),
        "intro": texts["intro"],
        "ignore_note": texts["ignore_note"],
    }
    subject = texts["subject"].format(code=code)
    text = render_to_string("kundalik/email/code.txt", context)
    html = render_to_string("kundalik/email/code.html", context)
    try:
        send_mail(subject, text, None, [user.email], html_message=html, fail_silently=False)
    except Exception:  # SMTP/tarmoq xatolari turlicha bo'ladi
        logger.exception("Kodni yuborib bo'lmadi (%s): %s", purpose, user.email)
        return False
    return True


def mask_email(email):
    local, _, domain = email.partition("@")
    if not domain:
        return email
    visible = local[:2] if len(local) > 4 else local[:1]
    return f"{visible}{'•' * 3}@{domain}"
