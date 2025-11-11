from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from api.admin_views import unapproved_items

urlpatterns = [
    path('', lambda request: HttpResponse("✅ Backend attivo e funzionante su Render!")),
    path('admin/', admin.site.urls),
    path('admin/unapproved/', unapproved_items, name='unapproved_items'),
    path('api/', include('api.urls')),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
]
