from django.db import models
from django_ckeditor_5.fields import CKEditor5Field
from django.utils.text import slugify

class Elonlar(models.Model):
    slug = models.SlugField(verbose_name="Elon uchun slug", unique=True, blank=True, max_length=155)
    title = models.CharField(verbose_name="Elon uchun sarlavha", max_length=500)
    description = CKEditor5Field('Elon haqida malumot')
    image = models.ImageField(upload_to='media/elonlar/', verbose_name="Elon uchun fotosurat")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            num = 1
            while Elonlar.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{num}"
                num += 1
            self.slug = slug
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'Elonlar'
