from django.db import models
from django_ckeditor_5.fields import CKEditor5Field

class Kutubxona(models.Model):
    title = models.CharField(verbose_name="Sarlavha ", max_length=500)
    author = models.CharField(verbose_name="Muallif ", max_length=500)
    image = models.ImageField(upload_to='media/kutubxona/' ,verbose_name="Fotosurat ")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
    class Meta:
        db_table = 'Kutubxona'
