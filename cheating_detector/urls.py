from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('webcam_feed/', views.webcam_feed, name='webcam_feed'),
    path('alerts/latest/', views.get_latest_alert, name='get_latest_alert'),
]
