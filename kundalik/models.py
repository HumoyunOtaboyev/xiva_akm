import secrets
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Sum
from django.db.models.functions import Lower
from django.utils import timezone
from django.utils.crypto import constant_time_compare, salted_hmac

MAX_BOOK_PAGES = 10000


class Author(models.Model):
    """Yozuvchi — umumiy katalog. Kitobxon qo'shgan yangi muallif admin tasdiqlaguncha faol emas."""

    name = models.CharField("Ismi", max_length=200)
    is_active = models.BooleanField(
        "Tasdiqlangan",
        default=False,
        help_text="Tasdiqlangan mualliflar barcha kitobxonlarning qidiruvida chiqadi.",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="Kim qo'shgan",
    )
    created_at = models.DateTimeField("Qo'shilgan vaqti", auto_now_add=True)

    class Meta:
        verbose_name = "Yozuvchi"
        verbose_name_plural = "Yozuvchilar"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(Lower("name"), name="kundalik_author_unique_name"),
        ]

    def __str__(self):
        return self.name


class Book(models.Model):
    """Kitob — umumiy katalog, har bir kitobxon unga `Reading` orqali bog'lanadi.

    Kitobxon qo'shgan yangi kitob admin tasdiqlaguncha faol emas: uni faqat
    qo'shgan odam ko'radi. Tasdiqlangach, hammaning qidiruvida chiqadi.
    """

    class Genre(models.TextChoices):
        NOVEL = "novel", "Roman"
        STORY = "story", "Hikoya / qissa"
        POETRY = "poetry", "She'riyat"
        HISTORY = "history", "Tarix"
        SCIENCE = "science", "Ilmiy"
        TECHNICAL = "technical", "Texnik"
        SELF_HELP = "self_help", "Shaxsiy rivojlanish"
        NON_FICTION = "non_fiction", "Hujjatli / ommabop"
        CHILDREN = "children", "Bolalar adabiyoti"
        OTHER = "other", "Boshqa"

    title = models.CharField("Nomi", max_length=300)
    author = models.ForeignKey(
        Author, on_delete=models.PROTECT, related_name="books", verbose_name="Yozuvchi"
    )
    pages = models.PositiveIntegerField(
        "Sahifalar soni",
        validators=[MinValueValidator(1), MaxValueValidator(MAX_BOOK_PAGES)],
    )
    genre = models.CharField("Janr", max_length=20, choices=Genre.choices, default=Genre.OTHER)
    is_active = models.BooleanField(
        "Tasdiqlangan",
        default=False,
        help_text="Tasdiqlangan kitoblar barcha kitobxonlarning qidiruvida chiqadi.",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="Kim qo'shgan",
    )
    created_at = models.DateTimeField("Qo'shilgan vaqti", auto_now_add=True)

    class Meta:
        verbose_name = "Kitob"
        verbose_name_plural = "Kitoblar"
        ordering = ["title"]
        constraints = [
            models.UniqueConstraint(
                Lower("title"), "author", name="kundalik_book_unique_title_author"
            ),
        ]

    def __str__(self):
        return f"{self.title} — {self.author}"

    def save(self, *args, **kwargs):
        pages_changed = False
        if self.pk:
            old_pages = Book.objects.filter(pk=self.pk).values_list("pages", flat=True).first()
            pages_changed = old_pages is not None and old_pages != self.pages
        super().save(*args, **kwargs)
        # Tasdiqlangan kitobning muallifi ham tasdiqlangan bo'lishi kerak.
        if self.is_active and not self.author.is_active:
            Author.objects.filter(pk=self.author_id).update(is_active=True)
            self.author.is_active = True
        # Sahifalar soni o'zgarsa, kitobxonlarning progressini qayta hisoblaymiz.
        if pages_changed:
            for reading in self.readings.all():
                reading.recalculate()


class Reading(models.Model):
    """Kitobxonning bitta kitob bo'yicha holati (progress, holat, tugatgan sana)."""

    class Status(models.TextChoices):
        WANT = "want", "O'qimoqchi"
        READING = "reading", "O'qimoqda"
        COMPLETED = "completed", "Tugatgan"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="readings",
        verbose_name="Kitobxon",
    )
    book = models.ForeignKey(
        Book, on_delete=models.CASCADE, related_name="readings", verbose_name="Kitob"
    )
    current_page = models.PositiveIntegerField("O'qilgan sahifa", default=0, editable=False)
    status = models.CharField(
        "Holati", max_length=20, choices=Status.choices, default=Status.WANT, editable=False
    )
    started_at = models.DateField("Boshlagan sana", null=True, blank=True, editable=False)
    finished_at = models.DateField("Tugatgan sana", null=True, blank=True, editable=False)
    created_at = models.DateTimeField("Qo'shilgan vaqti", auto_now_add=True)

    class Meta:
        verbose_name = "Kitobxon kitobi"
        verbose_name_plural = "Kitobxonlar kitoblari"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "book"], name="kundalik_reading_unique_user_book"),
        ]

    def __str__(self):
        return f"{self.user} — {self.book.title}"

    @property
    def percent(self):
        if not self.book.pages:
            return 0
        return round(self.current_page * 100 / self.book.pages)

    def recalculate(self):
        """Progress, holat va tugatgan sanani yozuvlardan qayta hisoblaydi."""
        total = 0
        finished = None
        first = None
        for log in self.logs.order_by("date", "id"):
            if first is None:
                first = log.date
            total += log.pages
            if finished is None and total >= self.book.pages:
                finished = log.date
        self.current_page = min(total, self.book.pages)
        if first and (self.started_at is None or first < self.started_at):
            self.started_at = first
        if self.current_page >= self.book.pages:
            self.status = self.Status.COMPLETED
            self.finished_at = finished
        elif self.current_page > 0 or self.started_at:
            self.status = self.Status.READING
            self.finished_at = None
        else:
            self.status = self.Status.WANT
            self.finished_at = None
        self.save(update_fields=["current_page", "status", "started_at", "finished_at"])


class ReadingLog(models.Model):
    """Kunlik o'qish yozuvi."""

    reading = models.ForeignKey(
        Reading, on_delete=models.CASCADE, related_name="logs", verbose_name="Kitob"
    )
    date = models.DateField("Sana", default=timezone.localdate)
    pages = models.PositiveIntegerField(
        "O'qilgan sahifa", validators=[MinValueValidator(1), MaxValueValidator(MAX_BOOK_PAGES)]
    )
    note = models.CharField("Izoh", max_length=300, blank=True)
    created_at = models.DateTimeField("Qo'shilgan vaqti", auto_now_add=True)

    class Meta:
        verbose_name = "O'qish yozuvi"
        verbose_name_plural = "O'qish yozuvlari"
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.date} — {self.pages} bet"

    def remaining_pages(self):
        used = (
            ReadingLog.objects.filter(reading_id=self.reading_id)
            .exclude(pk=self.pk)
            .aggregate(total=Sum("pages"))["total"]
            or 0
        )
        return max(self.reading.book.pages - used, 0)

    def clean(self):
        errors = {}
        if self.date and self.date > timezone.localdate():
            errors["date"] = ValidationError("Kelajakdagi sana kiritib bo'lmaydi.", code="date_future")
        if self.reading_id and self.pages:
            remaining = self.remaining_pages()
            if remaining <= 0:
                errors["pages"] = ValidationError(
                    "Bu kitob allaqachon tugallangan.", code="already_completed"
                )
            elif self.pages > remaining:
                errors["pages"] = ValidationError(
                    "Kitobda faqat %(max)s bet qolgan.",
                    code="pages_exceed",
                    params={"max": remaining},
                )
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.reading.recalculate()

    def delete(self, *args, **kwargs):
        reading = self.reading
        result = super().delete(*args, **kwargs)
        reading.recalculate()
        return result


class EmailCode(models.Model):
    """Emailga yuboriladigan 6 xonali kod (umumiy qism).

    Kodning o'zi saqlanmaydi — faqat HMAC xeshi. Ishlatilgach yozuv o'chiriladi.
    """

    CODE_TTL = timedelta(minutes=15)
    RESEND_COOLDOWN = timedelta(seconds=60)
    MAX_ATTEMPTS = 5
    HASH_SALT = "kundalik.email-code"

    code_hash = models.CharField(max_length=128, editable=False)
    expires_at = models.DateTimeField("Kod amal qiladi")
    attempts = models.PositiveSmallIntegerField("Noto'g'ri urinishlar", default=0)
    last_sent_at = models.DateTimeField("Oxirgi yuborilgan vaqt")
    created_at = models.DateTimeField("Yaratilgan vaqti", auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def __str__(self):
        return str(self.user)

    @classmethod
    def _hash(cls, user_id, code):
        return salted_hmac(cls.HASH_SALT, f"{user_id}:{code}").hexdigest()

    @classmethod
    def issue(cls, user):
        """Yangi kod yaratadi (eskisi bekor bo'ladi). (yozuv, kod) qaytaradi."""
        code = f"{secrets.randbelow(10 ** 6):06d}"
        now = timezone.now()
        record, _ = cls.objects.update_or_create(
            user=user,
            defaults={
                "code_hash": cls._hash(user.pk, code),
                "expires_at": now + cls.CODE_TTL,
                "attempts": 0,
                "last_sent_at": now,
            },
        )
        return record, code

    def seconds_until_resend(self):
        remaining = (self.last_sent_at + self.RESEND_COOLDOWN - timezone.now()).total_seconds()
        return max(0, int(remaining + 0.999))

    def can_resend(self):
        return self.seconds_until_resend() == 0

    @property
    def attempts_left(self):
        return max(0, self.MAX_ATTEMPTS - self.attempts)

    def check_code(self, code):
        """"ok", "invalid", "expired" yoki "too_many" qaytaradi."""
        if self.attempts >= self.MAX_ATTEMPTS:
            return "too_many"
        if timezone.now() > self.expires_at:
            return "expired"
        if constant_time_compare(self._hash(self.user_id, code), self.code_hash):
            return "ok"
        self.attempts += 1
        self.save(update_fields=["attempts"])
        return "too_many" if self.attempts >= self.MAX_ATTEMPTS else "invalid"


class EmailVerification(EmailCode):
    """Ro'yxatdan o'tgan, lekin emailini hali tasdiqlamagan kitobxon uchun kod."""

    HASH_SALT = "kundalik.email-verification"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="email_verification",
        verbose_name="Foydalanuvchi",
    )

    class Meta(EmailCode.Meta):
        verbose_name = "Email tasdiqlash"
        verbose_name_plural = "Email tasdiqlashlar (kutilmoqda)"

    @classmethod
    def is_pending(cls, user):
        return not user.is_active and cls.objects.filter(user=user).exists()


class PasswordResetCode(EmailCode):
    """Parolni tiklash uchun emailga yuborilgan kod."""

    HASH_SALT = "kundalik.password-reset"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="password_reset_code",
        verbose_name="Foydalanuvchi",
    )

    class Meta(EmailCode.Meta):
        verbose_name = "Parol tiklash kodi"
        verbose_name_plural = "Parol tiklash kodlari"
