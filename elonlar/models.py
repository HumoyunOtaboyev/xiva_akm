from django.db import models
from django.utils.text import slugify

class Elonlar(models.Model):
    title = models.CharField(verbose_name="Sarlavha ", max_length=100)
    description = models.CharField(verbose_name="description ", max_length=500)
    image = models.ImageField(upload_to='media/kutubxona/' ,verbose_name="Fotosurat ")
    
    def __str__(self):
        return self.title

    class Meta:
        db_table = 'Elonlar'
