from django.contrib import admin
from .models import NovedadEstadistica, AmpliacionEstadistica

@admin.register(NovedadEstadistica)
class NovedadEstadisticaAdmin(admin.ModelAdmin):
    # Columnas que verás en la lista
    list_display = ('nro', 'dependencia_alias', 'fecha_ingreso', 'titulo', 'aclarada')
    # Filtros laterales
    list_filter = ('dependencia_alias', 'aclarada', 'fecha_ingreso')
    # Buscador por número o título
    search_fields = ('nro', 'titulo', 'dependencia_original')
    # Orden descendente (más nuevos primero)
    ordering = ('-fecha_ingreso',)

@admin.register(AmpliacionEstadistica)
class AmpliacionEstadisticaAdmin(admin.ModelAdmin):
    list_display = ('nro', 'denuncia_madre', 'periodo', 'dependencia_alias', 'tipo')
    list_filter = ('periodo', 'dependencia_alias', 'tipo')
    search_fields = ('nro', 'denuncia_madre', 'titulo')
    ordering = ('-periodo', '-nro')