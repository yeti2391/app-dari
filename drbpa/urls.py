from django.urls import path
from . import views

app_name = 'drbpa'

urlpatterns = [
    path('', views.drbpa_home, name='home'),
    path('nuevo/', views.nuevo_registro, name='nuevo_registro'), # URL para el formulario
    
    # API endpoints para Vue
    path('api/maestros-drbpa/', views.api_maestros_drbpa, name='api_maestros'),
    path('api/guardar-ficha/', views.api_guardar_ficha, name='api_guardar'),
]