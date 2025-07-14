from django.urls import path
from .views import *

urlpatterns = [
    path("", TadbirlarListView.as_view(), name="tadbirlar"),
]
