from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Sum
from django.db.models.functions import Lower
from django.utils import timezone

MAX_BOOK_PAGES = 10000


class Author(models.Model):
    """Yozuvchi — bir nechta kitob va kitobxonlar uchun umumiy."""

    name = models.CharField("Ismi", max_length=200)
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
    """Kitob — umumiy katalog, har bir kitobxon unga `Reading` orqali bog'lanadi."""

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
        for log in self.logs.order_by("date", "id"):
            total += log.pages
            if finished is None and total >= self.book.pages:
                finished = log.date
        self.current_page = min(total, self.book.pages)
        if self.current_page >= self.book.pages:
            self.status = self.Status.COMPLETED
            self.finished_at = finished
        elif self.current_page > 0:
            self.status = self.Status.READING
            self.finished_at = None
        else:
            self.status = self.Status.WANT
            self.finished_at = None
        self.save(update_fields=["current_page", "status", "finished_at"])


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
