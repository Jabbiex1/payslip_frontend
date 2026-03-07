from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),  # Default Django admin (superuser)
    path('', include('payslip_app.urls')),  
        # Your app URLs
]
from django.contrib import admin

urlpatterns = [
    path("x92k-secret-admin/", admin.site.urls),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)