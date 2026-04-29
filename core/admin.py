from django.contrib import admin
from .models import *

# =============================================================================
# CONFIGURACIÓN DE VISTAS INLINE
# Estas clases permiten editar modelos relacionados desde la misma ficha principal.
# =============================================================================

class IdentificacionInline(admin.TabularInline):
    """Permite gestionar los documentos de una persona sin salir de su perfil."""
    model = Identificacion
    extra = 0 # No muestra filas vacías extras por defecto

class AliasInline(admin.TabularInline):
    """Permite gestionar los apodos de una persona desde su perfil."""
    model = Alias
    extra = 0

class ExpedientePersonaInline(admin.TabularInline):
    """Muestra qué personas están vinculadas a un expediente desde la vista del expediente."""
    model = ExpedientePersona
    extra = 0
    autocomplete_fields = ['persona'] # Requiere que PersonaAdmin tenga search_fields

# =============================================================================
# CONFIGURACIÓN DE MODELOS PRINCIPALES (ADMIN CLASSES)
# =============================================================================

class PersonaAdmin(admin.ModelAdmin):
    """
    Configuración para el modelo Persona.
    Incluye auditoría automática y gestión de documentos/alias.
    """
    # 1. Columnas visibles en el listado general
    list_display = ('primer_nombre', 'primer_apellido', 'documento_principal', 'fecha_registro', 'created_by')
    
    # 2. Campos que no se pueden editar manualmente (Auditoría)
    # IMPORTANTE: fecha_registro usa auto_now_add, por lo que DEBE ser readonly para verse.
    readonly_fields = ('fecha_registro', 'created_by')
    
    # 3. Herramientas de búsqueda y filtrado
    search_fields = ('primer_nombre', 'primer_apellido', 'identificaciones__numero')
    list_filter = ('fecha_registro', 'nacionalidad', 'created_by')
    
    # 4. Integración de modelos relacionados (Inlines)
    inlines = [IdentificacionInline, AliasInline]

    def documento_principal(self, obj):
        """Método auxiliar para mostrar el primer documento registrado en la lista general."""
        doc = obj.identificaciones.first()
        return f"{doc.tipo_documento.nombre}: {doc.numero}" if doc else "---"
    
    documento_principal.short_description = "Identificación"

admin.site.register(Persona, PersonaAdmin)


class ExpedienteAdmin(admin.ModelAdmin):
    """
    Configuración para el modelo Expediente.
    Muestra quién lo creó y permite ver a las personas vinculadas.
    """
    list_display = ('codigo', 'fecha_ingreso', 'oficina', 'subido_alfresco', 'created_by')
    
    # El campo created_by se asigna por código en la View, aquí se deja solo lectura.
    readonly_fields = ('created_by',)
    
    # Filtros rápidos para el panel lateral
    list_filter = ('oficina', 'subido_alfresco', 'fecha_ingreso')
    
    # Permite buscar expedientes por código rápidamente
    search_fields = ('codigo', 'observaciones')
    
    # Muestra la lista de personas involucradas al final de la ficha del expediente
    inlines = [ExpedientePersonaInline]

admin.site.register(Expediente, ExpedienteAdmin)


class ExpedienteMovimientoAdmin(admin.ModelAdmin):
    """Configuración para la trazabilidad de traslados."""
    list_display = ('expediente', 'origen', 'destino', 'fecha', 'entregado_por', 'recibido_por')
    list_filter = ('fecha', 'origen', 'destino')
    search_fields = ('expediente__codigo', 'entregado_por', 'recibido_por')

admin.site.register(ExpedienteMovimiento, ExpedienteMovimientoAdmin)

# =============================================================================
# REGISTROS SIMPLES (TABLAS MAESTRAS)
# Modelos que no requieren una configuración compleja para su gestión.
# =============================================================================

admin.site.register(Pais)
admin.site.register(TipoDocumento)
admin.site.register(Oficina)

# Nota: Alias e Identificacion se gestionan preferentemente 
# a través de los Inlines en PersonaAdmin, pero se pueden registrar si es necesario.
# admin.site.register(Alias)
# admin.site.register(Identificacion)