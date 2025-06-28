from django.contrib import admin
from .models import News

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('title', 'slug', 'content')
    prepopulated_fields = {'slug': ('title',)}
    # readonly_fields = ('created_at',)
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'content', 'card_image', 'created_at')
        }),
    )
