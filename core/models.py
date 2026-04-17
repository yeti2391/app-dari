from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Pais(models.Model):
    # BASADO EN ISO 3166 y se agrega OTRO con codigos XX y XXX para casos no identificados
    # ISO 3166 Alpha-2 (Ej: UY)
    codigo_alpha2 = models.CharField(max_length=2, unique=True, null=True, blank=True)
    # ISO 3166 Alpha-3 (Ej: URY)
    codigo_alpha3 = models.CharField(max_length=3, unique=True, null=True, blank=True)
    # Nombre oficial
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.nombre} ({self.codigo_alpha2})"

    class Meta:
        verbose_name_plural = "Países"
        ordering = ['nombre']


class TipoDocumento(models.Model):
    nombre = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre


class Oficina(models.Model):
    codigo = models.CharField(max_length=10, unique=True)
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre


class Persona(models.Model):
    # Todos los nombres son opcionales para soportar registros parciales o solo por Alias
    primer_nombre = models.CharField(max_length=100, blank=True, null=True)
    segundo_nombre = models.CharField(max_length=100, blank=True, null=True)
    primer_apellido = models.CharField(max_length=100, blank=True, null=True)
    segundo_apellido = models.CharField(max_length=100, blank=True, null=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    nacionalidad = models.ForeignKey(Pais, on_delete=models.PROTECT, blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        # Intentamos armar el nombre
        nombre = f"{self.primer_nombre or ''} {self.primer_apellido or ''}".strip()
        if not nombre:
            # Si no hay nombre, intentamos mostrar el primer alias
            p_alias = self.aliases.first()
            return f"ALIAS: {p_alias.alias}" if p_alias else f"ID: {self.id}"
        return nombre

    def save(self, *args, **kwargs):
        # Normalizamos TODOS los campos de texto a Mayúsculas automáticamente
        if self.primer_nombre: self.primer_nombre = self.primer_nombre.upper().strip()
        if self.segundo_nombre: self.segundo_nombre = self.segundo_nombre.upper().strip()
        if self.primer_apellido: self.primer_apellido = self.primer_apellido.upper().strip()
        if self.segundo_apellido: self.segundo_apellido = self.segundo_apellido.upper().strip()
        super(Persona, self).save(*args, **kwargs)

class Identificacion(models.Model):
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE, related_name='identificaciones')
    tipo_documento = models.ForeignKey(TipoDocumento, on_delete=models.PROTECT)
    numero = models.CharField(max_length=50)

    class Meta:
        # Un mismo número de un mismo tipo no puede repetirse en el sistema
        unique_together = ('tipo_documento', 'numero')

    def save(self, *args, **kwargs):
        if self.numero:
            self.numero = self.numero.upper().strip()
        super().save(*args, **kwargs)
        
class Alias(models.Model):
    # 'related_name' permite acceder desde Persona como persona.aliases.all()
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE, related_name='aliases')
    alias = models.CharField(max_length=150)

    def save(self, *args, **kwargs):
        # Los alias también se guardan siempre en mayúsculas para búsquedas precisas
        if self.alias:
            self.alias = self.alias.upper().strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.alias


class Expediente(models.Model):
    codigo = models.CharField(max_length=10, unique=True)
    fecha_ingreso = models.DateField()
    observaciones = models.TextField(blank=True, null=True)
    oficina = models.ForeignKey(Oficina, on_delete=models.PROTECT)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    subido_alfresco = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # Forzar mayúsculas y quitar espacios en blanco antes de guardar
        if self.codigo:
            self.codigo = self.codigo.upper().strip()
        super(Expediente, self).save(*args, **kwargs)

    def __str__(self):
        return self.codigo


class ExpedientePersona(models.Model):
    ROLES = [
        ('indagado', 'Indagado'),
        ('victima', 'Víctima'),
        ('denunciante', 'Denunciante'),
        ('testigo', 'Testigo'),
        ('otro', 'Otro'),
    ]

    expediente = models.ForeignKey(Expediente, on_delete=models.CASCADE)
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE)
    rol = models.CharField(max_length=20, choices=ROLES)

    def __str__(self):
        return f"{self.persona} - {self.rol}"

class ExpedienteMovimiento(models.Model):
    expediente = models.ForeignKey(Expediente, on_delete=models.CASCADE)
    # Registramos de qué oficina sale y a cuál entra
    origen = models.ForeignKey(Oficina, on_delete=models.PROTECT, related_name='movimientos_origen')
    destino = models.ForeignKey(Oficina, on_delete=models.PROTECT, related_name='movimientos_destino')
    
    fecha = models.DateTimeField() # Fecha y hora manual del traspaso real
    entregado_por = models.CharField(max_length=150)
    recibido_por = models.CharField(max_length=150)
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.expediente}: {self.origen} -> {self.destino}"