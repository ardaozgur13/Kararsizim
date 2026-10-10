"""
URL configuration for kararsizim project.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('', include('polls.urls')),
]

# Özel Hata Sayfaları (DEBUG=False durumunda Django tarafından tetiklenir)
handler404 = 'polls.views.custom_404_view'
handler500 = 'polls.views.custom_500_view'
handler403 = 'polls.views.custom_403_view'
handler400 = 'polls.views.custom_400_view'
