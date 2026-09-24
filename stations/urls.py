from django.urls import path
from . import views

urlpatterns = [
    path('map/', views.live_map_view, name='live_map'),
    path('list/', views.stations_list_view, name='stations_list'),
    path('<int:pk>/', views.station_detail_view, name='station_detail'),
    path('api/all/', views.api_stations_data, name='api_stations_data'),
    path('api/<int:station_id>/points/', views.api_station_points, name='api_station_points'),
]
