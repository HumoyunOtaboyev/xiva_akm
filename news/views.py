from django.views.generic import ListView, DetailView
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from .models import News, Tag   


class NewsListView(ListView):
    model = News
    template_name = "news/news.html"
    context_object_name = "news_list"
    paginate_by = 10

    def get_queryset(self):
        return News.objects.all().order_by('-created_at')


class NewsDetailView(DetailView):
    model = News
    template_name = "news/detail.html"
    context_object_name = "news_detail"
    slug_field = 'slug'
    slug_url_kwarg = 'slug'


# ✅ 1️⃣ TAG LIST (faqat taglar ro‘yxati)
def tag_list(request):
    tags = Tag.objects.all().order_by('name')  

    paginator = Paginator(tags, 10)
    page_number = request.GET.get('page')  
    page_obj = paginator.get_page(page_number)

    return render(request, 'tags.html', {
        'page_obj': page_obj
    })



def tag_detail(request, slug):
    tag = get_object_or_404(Tag, slug=slug)

    news_list = tag.news_articles.all().order_by('-created_at')

    paginator = Paginator(news_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'tag_detail.html', {
        'tag': tag,
        'page_obj': page_obj
    })