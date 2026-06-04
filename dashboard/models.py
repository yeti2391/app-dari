from django.db import models

class NovedadEstadistica(models.Model):
    """Información procesada de Eventos SGSP"""
    nro = models.BigIntegerField(unique=True, primary_key=True)
    nunc = models.CharField(max_length=50, null=True, blank=True)
    fecha_ingreso = models.DateTimeField(db_index=True)
    dependencia_original = models.CharField(max_length=255)
    dependencia_alias = models.CharField(max_length=50, db_index=True) # DARI, DCI, etc.
    titulo = models.CharField(max_length=255, db_index=True)
    aclarada = models.BooleanField(default=False)
    # Estadísticas de allanamientos
    allanamientos_pos = models.IntegerField(default=0)
    allanamientos_neg = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.nro} - {self.dependencia_alias}"

class AmpliacionEstadistica(models.Model):
    """Información procesada de Ampliaciones e Informes"""
    nro = models.BigIntegerField(unique=True, primary_key=True)
    denuncia_madre = models.BigIntegerField(db_index=True)
    fecha_denuncia = models.DateTimeField(null=True, blank=True)
    titulo = models.CharField(max_length=255)
    dependencia_alias = models.CharField(max_length=50, db_index=True)
    tipo = models.CharField(max_length=10) # AMP o IA
    periodo = models.CharField(max_length=7, db_index=True) # YYYY-MM
    # Estadísticas de allanamientos
    allanamientos_pos = models.IntegerField(default=0)
    allanamientos_neg = models.IntegerField(default=0)

    def __str__(self):
        return f"Amp {self.nro} de {self.denuncia_madre}"