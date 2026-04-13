# from django.urls import path
# from .views import home
# 
# urlpatterns = [
#     path('', home, name='home'),
# ]

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    
    # Endpoints de API para Vue
    path('api/buscar/', views.buscar_expedientes, name='api_buscar'),
    path('api/expediente/<int:id>/', views.detalle_expediente, name='api_detalle'),
    path('api/expediente/<int:id>/alfresco/', views.actualizar_alfresco, name='api_alfresco'),
    path('api/expediente/crear/', views.crear_expediente, name='api_crear'),
    path('api/oficinas/', views.lista_oficinas, name='api_oficinas'),
    path('api/paises/', views.lista_paises, name='api_paises'),
    path('api/tipos-documento/', views.lista_tipos_documento, name='api_tipos_documento'),  
    path('api/recientes/', views.expedientes_recientes, name='api_recientes'),

     # NUEVAS RUTAS DE MOVIMIENTOS
    path('api/movimientos/registrar/', views.registrar_movimiento, name='api_mov_registrar'),
    path('api/movimientos/historial/', views.historial_movimientos, name='api_mov_historial'),

    # REGISTRAR PERSONAS
    path('api/expediente/<int:id>/vincular-persona/', views.vincular_persona, name='api_vincular_persona'),
]
