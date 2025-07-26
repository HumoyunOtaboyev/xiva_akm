from django.urls import path
from .views import ElonlarListView

urlpatterns = [
    path("", ElonlarListView.as_view(), name="elonlar"),
]
