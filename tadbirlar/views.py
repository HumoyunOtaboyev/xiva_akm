from django.shortcuts import render
from django.views.generic import ListView, DetailView
from .models import *
# Create your views here.
class TadbirlarListView(ListView):
    model = Tadbirlar
    template_name = "tadbirlar/tadbirlar.html"
    context_object_name = "tadbirlar_list"
    paginate_by = 10  # Optional: adds pagination

    def get_queryset(self):
        # You can filter or order the queryset if needed
        return Tadbirlar.objects.all().order_by('-id')
    