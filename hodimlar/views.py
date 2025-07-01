from django.shortcuts import render
from django.views.generic import ListView, DetailView
from .models import *
# Create your views here.
class HodimlarListView(ListView):
    model = Hodimlar
    template_name = "hodimlar/hodimlar.html"
    context_object_name = "hodimlar_list"
    paginate_by = 10  # Optional: adds pagination

    def get_queryset(self):
        # You can filter or order the queryset if needed
        return Hodimlar.objects.all().order_by('-created_at')