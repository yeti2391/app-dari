# dashboard/models.py
from django.db import models

class ImportacionSGSP(models.Model):
    """Para llevar un registro de cuándo se subieron los datos"""
    fecha_carga = models.DateTimeField(auto_now_add=True)
    periodo_desde = models.DateField()
    periodo_hasta = models.DateField()
    usuario = models.ForeignKey('auth.User', on_delete=models.CASCADE)

class NovedadSGSP(models.Model):
    nro = models.BigIntegerField(primary_key=True)
    nunc = models.CharField(max_length=50, null=True, blank=True)
    fecha_ingreso = models.DateTimeField()
    dependencia = models.CharField(max_length=200)
    titulo = models.CharField(max_length=200)
    aclarada = models.BooleanField(default=False)
    # Relación con la carga
    importacion = models.ForeignKey(ImportacionSGSP, on_delete=models.CASCADE)

class AmpliacionSGSP(models.Model):
    nro = models.BigIntegerField(primary_key=True)
    denuncia_madre = models.BigIntegerField()
    dependencia = models.CharField(max_length=200)
    tipo = models.CharField(max_length=50) # AMP o IA
    importacion = models.ForeignKey(ImportacionSGSP, on_delete=models.CASCADE)

class PersonaSGSP(models.Model):
    cedula = models.CharField(max_length=50, null=True)
    nombre = models.CharField(max_length=255)
    rol = models.CharField(max_length=100)
    evento_nro = models.BigIntegerField()
    allanamiento_pos = models.IntegerField(default=0)
    allanamiento_neg = models.IntegerField(default=0)
    importacion = models.ForeignKey(ImportacionSGSP, on_delete=models.CASCADE)