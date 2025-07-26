from django.shortcuts import render

# Create your views here.
def index(request):
    return render(request, 'index.html')

    
def AboutUs(request):
    return render(request, 'aboutUs/aboutUs.html')