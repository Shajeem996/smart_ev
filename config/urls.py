"""
URL Configuration for Smart EV Charging Slot Booking & Queue Scheduler.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Built-in Admin (Staff/Superuser access)
    path('django-admin/', admin.site.urls),

    # Dashboard & Landing routes
    path('', include('dashboard.urls')),

    # Accounts / Auth routes
    path('auth/', include('accounts.urls')),

    # Stations & Map routes
    path('stations/', include('stations.urls')),

    # Vehicles routes
    path('vehicles/', include('vehicles.urls')),

    # Bookings routes
    path('bookings/', include('bookings.urls')),
    path('book/', include('bookings.urls')), # shortcut /book/

    # Charging sessions & Operator routes
    path('operator/', include('charging.urls')),

    # Queue management routes
    path('queue/', include('queue_management.urls')),

    # Notifications routes
    path('notifications/', include('notifications.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
