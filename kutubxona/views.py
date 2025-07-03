from django.shortcuts import render
from django.views.generic import ListView, DetailView
from .models import *
# Create your views here.
class KutubxonaListView(ListView):
    model = Kutubxona
    template_name = "kutubxona/kutubxona.html"
    context_object_name = "kutubxona_list"
    paginate_by = 10  

    def get_queryset(self):
        return Kutubxona.objects.all().order_by('-created_at')