from django.contrib import admin
from django.urls import path, include
from api.admin_views import unapproved_items

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin/unapproved/', unapproved_items, name='unapproved_items'),
    path('api/', include('api.urls')),

    # Aggiungi queste due righe:
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
]
