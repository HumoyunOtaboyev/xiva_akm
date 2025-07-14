from django.contrib import admin
from .models import *
# Register your models here.
class TadbirlarAdmin(admin.ModelAdmin):
    list_display = ('id','title',)
    search_fields = ('id','title','date')
    fields = ('title', 'date', 'place', )
    ordering = ('-created_at',)

admin.site.register(Tadbirlar,TadbirlarAdmin)