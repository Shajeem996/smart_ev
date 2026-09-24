from django.urls import path
from . import views

urlpatterns = [
    path('', views.user_queue_view, name='user_queue'),
    path('join/', views.join_queue_view, name='join_queue'),
    path('<int:pk>/cancel/', views.cancel_queue_view, name='cancel_queue'),
]
