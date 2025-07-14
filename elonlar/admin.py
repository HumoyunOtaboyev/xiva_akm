from django.contrib import admin
from .models import *
# Register your models here.
class ElonlarAdmin(admin.ModelAdmin):
    list_display = ('id','title',)
    search_fields = ('id','title','description')
    fields = ('title', 'description', 'image', )
    # ordering = ('-created_at',)

admin.site.register(Elonlar,ElonlarAdmin)