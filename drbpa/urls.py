from django.urls import path
from . import views

app_name = 'drbpa'

urlpatterns = [
    path('', views.drbpa_home, name='home'),
]