from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = "kundalik"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("kirish/", views.KundalikLoginView.as_view(), name="login"),
    path("royxatdan-otish/", views.register, name="register"),
    path("chiqish/", LogoutView.as_view(next_page="home"), name="logout"),

    path("api/kitoblar/", views.add_book, name="api_add_book"),
    path("api/kitoblar/<int:pk>/ochirish/", views.delete_book, name="api_delete_book"),
    path("api/yozuvlar/", views.add_log, name="api_add_log"),
    path("api/yozuvlar/<int:pk>/ochirish/", views.delete_log, name="api_delete_log"),
]
