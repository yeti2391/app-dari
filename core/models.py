from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Pais(models.Model):
    codigo = models.CharField(max_length=10, unique=True)
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre


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
    documento = models.CharField(max_length=20)
    tipo_documento = models.ForeignKey(TipoDocumento, on_delete=models.PROTECT)
    primer_nombre = models.CharField(max_length=100)
    segundo_nombre = models.CharField(max_length=100, blank=True, null=True)
    primer_apellido = models.CharField(max_length=100)
    segundo_apellido = models.CharField(max_length=100, blank=True, null=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    nacionalidad = models.ForeignKey(Pais, on_delete=models.PROTECT)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.primer_nombre} {self.primer_apellido}"


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