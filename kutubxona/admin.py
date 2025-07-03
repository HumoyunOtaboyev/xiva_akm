from django.contrib import admin
from .models import *
# Register your models here.
class KutubxonaAdmin(admin.ModelAdmin):
    list_display = ('id','title','created_at')
    search_fields = ('id','title','author')
    fields = ('title', 'author', 'image')
    ordering = ('-created_at',)

admin.site.register(Kutubxona,KutubxonaAdmin)