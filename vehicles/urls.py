from django.urls import path
from . import views

urlpatterns = [
    path('', views.vehicle_list_view, name='vehicle_list'),
    path('add/', views.vehicle_create_view, name='vehicle_add'),
    path('<int:pk>/edit/', views.vehicle_edit_view, name='vehicle_edit'),
    path('<int:pk>/delete/', views.vehicle_delete_view, name='vehicle_delete'),
]
