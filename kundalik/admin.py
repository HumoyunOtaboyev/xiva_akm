from django.contrib import admin
from django.db.models import Count

from .models import Author, Book, Reading, ReadingLog


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("name", "book_count", "created_at")
    search_fields = ("name",)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_book_count=Count("books"))

    @admin.display(description="Kitoblar soni", ordering="_book_count")
    def book_count(self, obj):
        return obj._book_count


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "pages", "genre", "reader_count", "created_by", "created_at")
    list_filter = ("genre",)
    search_fields = ("title", "author__name")
    autocomplete_fields = ("author",)
    readonly_fields = ("created_by", "created_at")

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("author", "created_by")
            .annotate(_reader_count=Count("readings"))
        )

    @admin.display(description="Kitobxonlar", ordering="_reader_count")
    def reader_count(self, obj):
        return obj._reader_count


class ReadingLogInline(admin.TabularInline):
    model = ReadingLog
    extra = 0
    fields = ("date", "pages", "note")
    ordering = ("-date", "-id")


@admin.register(Reading)
class ReadingAdmin(admin.ModelAdmin):
    list_display = ("user", "book", "status", "progress", "finished_at", "created_at")
    list_filter = ("status", "book__genre")
    search_fields = ("user__username", "user__first_name", "user__email", "book__title", "book__author__name")
    autocomplete_fields = ("book",)
    readonly_fields = ("current_page", "status", "finished_at", "created_at")
    inlines = (ReadingLogInline,)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "book__author")

    @admin.display(description="Progress")
    def progress(self, obj):
        return f"{obj.current_page} / {obj.book.pages} ({obj.percent}%)"

    def save_formset(self, request, form, formset, change):
        super().save_formset(request, form, formset, change)
        # Inline o'chirishlar delete() ni chetlab o'tishi mumkin — qayta hisoblaymiz.
        form.instance.recalculate()


@admin.register(ReadingLog)
class ReadingLogAdmin(admin.ModelAdmin):
    list_display = ("date", "reader", "book_title", "pages", "note")
    list_filter = ("date",)
    search_fields = ("note", "reading__book__title", "reading__user__username", "reading__user__email")
    autocomplete_fields = ("reading",)
    date_hierarchy = "date"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("reading__user", "reading__book")

    @admin.display(description="Kitobxon", ordering="reading__user__username")
    def reader(self, obj):
        return obj.reading.user

    @admin.display(description="Kitob", ordering="reading__book__title")
    def book_title(self, obj):
        return obj.reading.book.title

    def delete_queryset(self, request, queryset):
        readings = {log.reading for log in queryset.select_related("reading__book")}
        super().delete_queryset(request, queryset)
        for reading in readings:
            reading.recalculate()
