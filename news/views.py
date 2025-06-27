from django.views.generic import ListView, DetailView

from news.models import News

class NewsListView(ListView):
    model = News
    template_name = "news/news.html"
    context_object_name = "news_list"


class NewsDetailView(DetailView):
    model = News
    template_name = "news/detail.html"
    context_object_name = "news_detail"

