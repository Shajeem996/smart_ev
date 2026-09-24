from django.urls import path
from . import views

urlpatterns = [
    path('station/', views.operator_station_view, name='operator_station'),
    path('points/', views.operator_points_view, name='operator_points'),
    path('points/<int:pk>/status/', views.operator_update_point_status, name='operator_point_status'),
    path('bookings/', views.operator_bookings_view, name='operator_bookings'),
    path('verify-qr/', views.operator_verify_qr_view, name='operator_verify_qr'),
    path('start/<int:booking_id>/', views.operator_start_charging, name='operator_start_charging'),
    path('end/<int:session_id>/', views.operator_end_charging, name='operator_end_charging'),
    path('sessions/', views.operator_sessions_view, name='operator_sessions'),
    path('queue/', views.operator_queue_view, name='operator_queue'),
    path('reports/', views.operator_reports_view, name='operator_reports'),
]
