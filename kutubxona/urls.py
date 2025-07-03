from django.urls import path

from .views import *

urlpatterns = [
    path("", KutubxonaListView.as_view(), name="kutubxona")
]