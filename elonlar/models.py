from django.db import models
from django_ckeditor_5.fields import CKEditor5Field

class Elonlar(models.Model):
    title = models.CharField(verbose_name="Elon uchun sarlavha ", max_length=500)
    description = CKEditor5Field('Elon haqida malumot ')
    image = models.ImageField(upload_to='media/elonlar/' ,verbose_name="Elon uchun fotosurat ")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
    class Meta:
        db_table = 'Elonlar'
