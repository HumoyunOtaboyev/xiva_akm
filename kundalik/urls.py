from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = "kundalik"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),

    # Kirish sayt ildiziga ko'chdi — eski havolalar ishlashda davom etsin.
    path("kirish/", RedirectView.as_view(pattern_name="accounts:login", query_string=True, permanent=True)),
    path("royxatdan-otish/", RedirectView.as_view(pattern_name="accounts:register", query_string=True, permanent=True)),

    path("api/kitoblar/", views.add_book, name="api_add_book"),
    path("api/kitoblar/qidirish/", views.search_books, name="api_search_books"),
    path("api/mualliflar/qidirish/", views.search_authors, name="api_search_authors"),
    path("api/kitoblar/<int:pk>/boshlash/", views.start_reading, name="api_start_reading"),
    path("api/kitoblar/<int:pk>/ochirish/", views.delete_book, name="api_delete_book"),
    path("api/yozuvlar/", views.add_log, name="api_add_log"),
    path("api/yozuvlar/<int:pk>/ochirish/", views.delete_log, name="api_delete_log"),
]
