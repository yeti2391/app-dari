from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(Pais)
admin.site.register(TipoDocumento)
admin.site.register(Oficina)
admin.site.register(Persona)
admin.site.register(Expediente)
admin.site.register(ExpedientePersona)
admin.site.register(TipoMovimiento)
admin.site.register(ExpedienteMovimiento)