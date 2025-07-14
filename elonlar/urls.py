from django.urls import path
from .views import ElonlarListView, ElonDetailView

urlpatterns = [
    path("", ElonlarListView.as_view(), name="elonlar"),
    path("detail/<int:pk>/", ElonDetailView.as_view(), name="elon_detail"),
]
