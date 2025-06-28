from django.db import models
from django_ckeditor_5.fields import CKEditor5Field
from django.utils import timezone
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
        # auto_now_add=True,
        verbose_name="Created At",
        help_text="Date and time when the news item was created.",
        default=timezone.now

    )
    class Meta:
        verbose_name = "News Article"
        verbose_name_plural = "News Articles"
        ordering = ['-created_at']
    def __str__(self):
        return self.title