from django.urls import path

from news.views import NewsListView, NewsDetailView

urlpatterns = [
    path("", NewsListView.as_view(), name="news"),
    path("<slug:slug>/", NewsDetailView.as_view(), name="news_detail"),
]