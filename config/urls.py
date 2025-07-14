from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from app.views import index
urlpatterns = [
    path("", index,name="home"),
    path('yangiliklar/', include("news.urls")),
    path('admin/', admin.site.urls),
    path("ckeditor5/", include('django_ckeditor_5.urls')),
    path('hodimlar/',include('hodimlar.urls')),
    path('elonlar/',include('elonlar.urls')),
    path('kutubxona/',include('kutubxona.urls')),
    path('tadbirlar/',include('tadbirlar.urls'))
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

