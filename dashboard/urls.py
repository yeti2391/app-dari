from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('importar/', views.importar_datos, name='importar'),
    path('informe/anual/', views.generar_informe_anual, name='informe_anual'),
]