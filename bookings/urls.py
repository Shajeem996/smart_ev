from django.urls import path
from . import views

urlpatterns = [
    path('', views.book_slot_view, name='book_slot'),
    path('my-bookings/', views.my_bookings_view, name='my_bookings'),
    path('<int:pk>/', views.booking_detail_view, name='booking_detail'),
    path('<int:pk>/cancel/', views.cancel_booking_view, name='cancel_booking'),
]
