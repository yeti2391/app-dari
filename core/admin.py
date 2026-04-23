from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(Pais)
admin.site.register(TipoDocumento)
admin.site.register(Oficina)
admin.site.register(Alias)
admin.site.register(ExpedientePersona)
admin.site.register(ExpedienteMovimiento)



class ExpedienteAdmin(admin.ModelAdmin):
    # Mostramos el creador en la lista del admin
    list_display = ('codigo', 'fecha_ingreso', 'oficina', 'created_by')
    # Hacemos que el campo sea de solo lectura para que no lo cambien a mano
    readonly_fields = ('created_by',)

admin.site.register(Expediente, ExpedienteAdmin)



class PersonaAdmin(admin.ModelAdmin):
    # Columnas visibles en la lista
    list_display = ('primer_nombre', 'primer_apellido', 'documento_principal', 'created_by')
    readonly_fields = ('created_by',)

    # Método auxiliar para mostrar el documento en la lista si lo deseas
    def documento_principal(self, obj):
        doc = obj.identificaciones.first()
        return f"{doc.tipo_documento.nombre}: {doc.numero}" if doc else "Sin Doc"

admin.site.register(Persona, PersonaAdmin)