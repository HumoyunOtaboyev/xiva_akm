from django.views.generic import ListView, DetailView
from .models import News

class NewsListView(ListView):
    model = News
    template_name = "news/news.html"
    context_object_name = "news_list"
    paginate_by = 10  # Optional: adds pagination

    def get_queryset(self):
        # You can filter or order the queryset if needed
        return News.objects.all().order_by('-created_at')

class NewsDetailView(DetailView):
    model = News
    template_name = "news/detail.html"
    context_object_name = "news_detail"
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
