from django.urls import path
from news.views import NewsListView, NewsDetailView, tag_list, tag_detail

urlpatterns = [
    path("", NewsListView.as_view(), name="yangiliklar"),
    path("<slug:slug>/", NewsDetailView.as_view(), name="news_detail"),

    path("tags/", tag_list, name="tag_list"),  # barcha taglar
    path("tag/<slug:slug>/", tag_detail, name="tag_detail"),  # bitta tag
]