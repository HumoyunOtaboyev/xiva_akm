from django.contrib import admin
from news.models import News, NewsImage

class NewsImageInline(admin.TabularInline):
    model = NewsImage
    extra = 1

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'description']
    inlines = [NewsImageInline]