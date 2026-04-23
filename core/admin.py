from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(Pais)
admin.site.register(TipoDocumento)
admin.site.register(Oficina)
admin.site.register(Persona)
admin.site.register(Alias)
admin.site.register(ExpedientePersona)
admin.site.register(ExpedienteMovimiento)



class ExpedienteAdmin(admin.ModelAdmin):
    # Mostramos el creador en la lista del admin
    list_display = ('codigo', 'fecha_ingreso', 'oficina', 'created_by')
    # Hacemos que el campo sea de solo lectura para que no lo cambien a mano
    readonly_fields = ('created_by',)

admin.site.register(Expediente, ExpedienteAdmin)