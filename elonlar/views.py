from django.shortcuts import render
from django.views.generic import ListView, DetailView
from .models import *
# Create your views here.
class ElonlarListView(ListView):
    model = Elonlar
    template_name = "elonlar/elonlar.html"
    context_object_name = "elonlar_list"
    paginate_by = 10  # Optional: adds pagination

    def get_queryset(self):
        # You can filter or order the queryset if needed
        return Elonlar.objects.all().order_by('-id')
    
class ElonDetailView(DetailView):
    model = Elonlar
    template_name = "elonlar/elon_detail.html"
    context_object_name = "elon"
    paginate_by = 10
