from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = "kundalik"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("kirish/", views.KundalikLoginView.as_view(), name="login"),
    path("royxatdan-otish/", views.register, name="register"),
    path("tasdiqlash/", views.verify_email, name="verify"),
    path("chiqish/", LogoutView.as_view(next_page="home"), name="logout"),

    path("api/kitoblar/", views.add_book, name="api_add_book"),
    path("api/kitoblar/qidirish/", views.search_books, name="api_search_books"),
    path("api/mualliflar/qidirish/", views.search_authors, name="api_search_authors"),
    path("api/kitoblar/<int:pk>/boshlash/", views.start_reading, name="api_start_reading"),
    path("api/kitoblar/<int:pk>/ochirish/", views.delete_book, name="api_delete_book"),
    path("api/yozuvlar/", views.add_log, name="api_add_log"),
    path("api/yozuvlar/<int:pk>/ochirish/", views.delete_log, name="api_delete_log"),
]
