from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_view, name='landing'),

    # Role Dashboards
    path('user/dashboard/', views.user_dashboard, name='user_dashboard'),
    path('operator/dashboard/', views.operator_dashboard, name='operator_dashboard'),
    path('admin-panel/dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # Admin Management
    path('admin-panel/users/', views.admin_users_list, name='admin_users'),
    path('admin-panel/users/<int:pk>/toggle/', views.admin_user_toggle_status, name='admin_user_toggle'),

    path('admin-panel/stations/', views.admin_stations_list, name='admin_stations'),
    path('admin-panel/stations/add/', views.admin_station_create, name='admin_station_create'),
    path('admin-panel/stations/<int:pk>/edit/', views.admin_station_edit, name='admin_station_edit'),
    path('admin-panel/stations/<int:pk>/delete/', views.admin_station_delete, name='admin_station_delete'),

    path('admin-panel/operators/', views.admin_operators_list, name='admin_operators'),
    path('admin-panel/operators/add/', views.admin_operator_create, name='admin_operator_create'),
    path('admin-panel/operators/<int:pk>/edit/', views.admin_operator_edit, name='admin_operator_edit'),
    path('admin-panel/operators/<int:pk>/toggle/', views.admin_operator_toggle, name='admin_operator_toggle'),

    path('admin-panel/charging-points/', views.admin_points_list, name='admin_points'),
    path('admin-panel/charging-points/add/', views.admin_point_create, name='admin_point_create'),
    path('admin-panel/charging-points/<int:pk>/edit/', views.admin_point_edit, name='admin_point_edit'),
    path('admin-panel/charging-points/<int:pk>/delete/', views.admin_point_delete, name='admin_point_delete'),

    path('admin-panel/bookings/', views.admin_bookings_list, name='admin_bookings'),
    path('admin-panel/sessions/', views.admin_sessions_list, name='admin_sessions'),
    path('admin-panel/queues/', views.admin_queue_list, name='admin_queues'),
    path('admin-panel/reports/', views.admin_reports_view, name='admin_reports'),
    path('admin-panel/settings/', views.admin_settings_view, name='admin_settings'),
]
