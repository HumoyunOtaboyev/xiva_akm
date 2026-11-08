"""Saytning umumiy kirish tizimi URL'lari (sayt ildizida, namespace: accounts)."""

from django.urls import path

from . import auth_views

app_name = "accounts"

urlpatterns = [
    path("kirish/", auth_views.SiteLoginView.as_view(), name="login"),
    path("chiqish/", auth_views.SiteLogoutView.as_view(), name="logout"),
    path("royxatdan-otish/", auth_views.register, name="register"),
    path("tasdiqlash/", auth_views.verify_email, name="verify"),
    path("parol-tiklash/", auth_views.password_reset_request, name="password_reset"),
    path("parol-tiklash/yangi-parol/", auth_views.password_reset_confirm, name="password_reset_confirm"),
]
