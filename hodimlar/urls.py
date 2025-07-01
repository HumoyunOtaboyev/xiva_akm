from django.urls import path

from .views import *

urlpatterns = [
    path("", HodimlarListView.as_view(), name="hodimlar")
]