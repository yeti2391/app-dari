from django.contrib import admin
from .models import DepartamentoUru, DependenciaPolicial, FichaAusente, HistorialFicha

# --- VISTAS INLINE ---
class DependenciaInline(admin.TabularInline):
    model = DependenciaPolicial
    extra = 1

class HistorialInline(admin.TabularInline):
    model = HistorialFicha
    extra = 0
    readonly_fields = ('usuario', 'fecha', 'accion', 'observaciones')
    can_delete = False

# --- CONFIGURACIÓN DE DEPARTAMENTOS ---
@admin.register(DepartamentoUru)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    inlines = [DependenciaInline]

@admin.register(DependenciaPolicial)
class DependenciaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'departamento')
    list_filter = ('departamento',)
    search_fields = ('nombre',)

# --- CONFIGURACIÓN DE FICHAS DE AUSENCIA ---
@admin.register(FichaAusente)
class FichaAusenteAdmin(admin.ModelAdmin):
    # CORRECCIÓN: Usamos métodos para traer el nombre desde el modelo Persona
    list_display = ('nro_caso', 'get_nombre', 'get_apellido', 'estado_investigacion', 'ingresado_por')
    
    # CORRECCIÓN: En el buscador debemos usar el prefijo 'persona__' para entrar a la otra tabla
    search_fields = ('nro_caso', 'persona__primer_nombre', 'persona__primer_apellido', 'persona__documento', 'nro_sgsp')
    
    list_filter = ('estado_investigacion', 'departamento_hecho', 'equipo')
    readonly_fields = ('ingresado_por', 'fecha_registro', 'edad_al_momento', 'franja_etaria')
    inlines = [HistorialInline]

    # --- MÉTODOS PARA ACCEDER A DATOS RELACIONADOS ---
    def get_nombre(self, obj):
        return obj.persona.primer_nombre
    get_nombre.short_description = 'Primer Nombre' # Título de la columna
    get_nombre.admin_order_field = 'persona__primer_nombre' # Permite ordenar

    def get_apellido(self, obj):
        return obj.persona.primer_apellido
    get_apellido.short_description = 'Primer Apellido'
    get_apellido.admin_order_field = 'persona__primer_apellido'

admin.site.register(HistorialFicha)