from django.urls import path
from . import views

urlpatterns = [
    path('', views.test),
    path('2', views.responseunity),
]