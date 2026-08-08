"""
URL configuration for HabotConnect LSA Service Booking project.
"""

from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    # Redirect root URL to interactive API documentation
    path('', RedirectView.as_view(url='/api/docs/', permanent=False), name='root-redirect'),

    path('admin/', admin.site.urls),
    path('api/v1/', include('bookings.urls', namespace='v1')),
    path('api/', include('bookings.urls', namespace='v0')),

    # API Documentation (drf-spectacular)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]


