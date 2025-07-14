from django.db import models
from django.utils.text import slugify

class Tadbirlar(models.Model):
    title = models.CharField(verbose_name="Sarlavha ", max_length=250)
    place = models.CharField(verbose_name="O'tkaziladigan joyi", max_length=250)
    date = models.DateTimeField(verbose_name="Tadbir o'tkaziladigan vaqti")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title

    class Meta:
        db_table = 'Tadbirlar'
