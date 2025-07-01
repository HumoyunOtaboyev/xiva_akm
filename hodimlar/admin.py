from django.contrib import admin
from .models import *
# Register your models here.
class HodimlarAdmin(admin.ModelAdmin):
    list_display = ('id','ismi','phone')
    search_fields = ('id','ismi','phone')
    fields = ('ismi', 'phone', 'lavozimi','telegram','image')
    ordering = ('-created_at',)

admin.site.register(Hodimlar,HodimlarAdmin)