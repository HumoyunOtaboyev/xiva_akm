from django.db import models

# Create your models here.
class Hodimlar(models.Model):
    ismi = models.CharField(verbose_name="Hodimning to'liq ismi: ", max_length=500)
    image = models.ImageField(upload_to='media/hodimlar/' ,verbose_name="Hodimning fotosurati: ")
    lavozimi = models.CharField(verbose_name="Hodimning lavozimi: ", max_length=500)
    phone = models.CharField(verbose_name="Hodimning telefon raqami: ", max_length=500)
    telegram = models.CharField(verbose_name="Hodimning telegram username: ", max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.ismi
    
    class Meta:
        db_table = 'Hodimlar'
