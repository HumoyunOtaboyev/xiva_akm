import logging

from django.core.mail import send_mail
from django.template.loader import render_to_string

from .models import EmailVerification

logger = logging.getLogger(__name__)


def send_verification_code(user, code):
    """Tasdiqlash kodini emailga yuboradi. Xatolik bo'lsa False qaytaradi (va logga yozadi)."""
    context = {
        "name": user.first_name or user.email,
        "code": code,
        "minutes": int(EmailVerification.CODE_TTL.total_seconds() // 60),
    }
    subject = f"{code} — Xiva shahar AKM tasdiqlash kodi"
    text = render_to_string("kundalik/email/verification_code.txt", context)
    html = render_to_string("kundalik/email/verification_code.html", context)
    try:
        send_mail(subject, text, None, [user.email], html_message=html, fail_silently=False)
    except Exception:  # SMTP/tarmoq xatolari turlicha bo'ladi
        logger.exception("Tasdiqlash kodini yuborib bo'lmadi: %s", user.email)
        return False
    return True


def mask_email(email):
    local, _, domain = email.partition("@")
    if not domain:
        return email
    visible = local[:2] if len(local) > 4 else local[:1]
    return f"{visible}{'•' * 3}@{domain}"
