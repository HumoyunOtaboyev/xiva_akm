from django.db import models
from django_ckeditor_5.fields import CKEditor5Field
from django.utils import timezone


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, max_length=100)

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"

    def __str__(self):
        return self.name


class News(models.Model):
    slug = models.SlugField("Slug", unique=True, blank=True, max_length=155)
    title = models.CharField(max_length=200)
    content = CKEditor5Field('Content')

    card_image = models.ImageField(
        upload_to='news_card_images/',
        blank=True,
        null=True,
        verbose_name="Card Image",
        help_text="Image displayed on the news card."
    )

    created_at = models.DateTimeField(
        verbose_name="Created At",
        help_text="Date and time when the news item was created.",
        default=timezone.now
    )

    tags = models.ManyToManyField(
        Tag,
        related_name='news_articles',
        blank=True
    )

    class Meta:
        verbose_name = "News Article"
        verbose_name_plural = "News Articles"
        ordering = ['-created_at']

    def __str__(self):
        return self.title