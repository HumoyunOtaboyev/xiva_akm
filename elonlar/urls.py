from django.urls import path

from .views import *

urlpatterns = [
    path("", ElonlarListView.as_view(), name="elonlar")
]