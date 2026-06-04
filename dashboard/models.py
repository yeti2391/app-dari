from django.db import models

# =============================================================================
# 1. TABLAS BASE (RAW DATA)
# Estas tablas reciben la importación directa de los archivos CSV.
# =============================================================================

class EventoSGSP(models.Model):
    """Mapeo exacto de exportados.eventossgsp"""
    nro = models.BigIntegerField(primary_key=True)
    noticiaunicacriminal = models.BigIntegerField(null=True, blank=True)
    hecho = models.DateTimeField(null=True, blank=True)
    conocimiento = models.DateTimeField(null=True, blank=True)
    ingreso = models.DateTimeField(null=True, blank=True)
    control = models.DateTimeField(null=True, blank=True)
    u_ejecutora_origen = models.CharField(max_length=255, null=True, blank=True)
    dependencia_origen = models.CharField(max_length=255, null=True, blank=True)
    usuario_ingreso = models.CharField(max_length=255, null=True, blank=True)
    u_ejecutora_actual = models.CharField(max_length=255, null=True, blank=True)
    dependencia_actual = models.CharField(max_length=255, null=True, blank=True)
    titulo = models.TextField(null=True, blank=True)
    jurisdiccion = models.CharField(max_length=255, null=True, blank=True)
    deptoevento = models.CharField(max_length=255, null=True, blank=True)
    complemento = models.CharField(max_length=255, null=True, blank=True)
    barrio = models.CharField(max_length=255, null=True, blank=True)
    nombre_ciudad_localidad = models.CharField(max_length=255, null=True, blank=True)
    direccion = models.TextField(null=True, blank=True)
    aclarada = models.CharField(max_length=10, null=True, blank=True)
    reservada = models.CharField(max_length=10, null=True, blank=True)
    tablet = models.CharField(max_length=10, null=True, blank=True)
    juzgados = models.CharField(max_length=255, null=True, blank=True)
    plazo = models.CharField(max_length=20, null=True, blank=True)
    x = models.FloatField(null=True, blank=True) # DOUBLE PRECISION en SQL
    y = models.FloatField(null=True, blank=True) # DOUBLE PRECISION en SQL
    medidasvictima = models.TextField(null=True, blank=True)
    medidasindagado = models.TextField(null=True, blank=True)
    medidasconductor = models.TextField(null=True, blank=True)
    custodiapolicial = models.CharField(max_length=10, null=True, blank=True)
    activa = models.CharField(max_length=10, null=True, blank=True)
    fechainiciocustodia = models.DateTimeField(null=True, blank=True)
    fechafincustodia = models.DateTimeField(null=True, blank=True)
    eventosivve = models.CharField(max_length=10, null=True, blank=True)
    total_seguimiento_area_investigaciones = models.IntegerField(null=True, blank=True)
    total_seguimiento_area_seguridad = models.IntegerField(null=True, blank=True)
    total_allanamientos_positivos = models.IntegerField(null=True, blank=True)
    total_allanamientos_negativos = models.IntegerField(null=True, blank=True)
    autoridades_intervinientes = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = '"exportados"."eventossgsp"' # Nota las comillas dobles para el schema


class AmpliacionInfo(models.Model):
    """Mapeo exacto de exportados.ampliacionesinformes"""
    nro = models.BigIntegerField(primary_key=True)
    denuncia = models.BigIntegerField()
    ingreso_denuncia = models.DateTimeField(null=True, blank=True)
    titulo = models.TextField(null=True, blank=True)
    departamento_hecho = models.CharField(max_length=255, null=True, blank=True)
    u_ejecutora_evento = models.CharField(max_length=255, null=True, blank=True)
    dependencia_evento = models.CharField(max_length=255, null=True, blank=True)
    u_ejecutora_ampliacion = models.CharField(max_length=255, null=True, blank=True)
    dependencia_ampliacion = models.CharField(max_length=255, null=True, blank=True)
    reservada = models.CharField(max_length=10, null=True, blank=True)
    tablet = models.CharField(max_length=10, null=True, blank=True)
    tipo = models.CharField(max_length=10, null=True, blank=True)
    seguimiento_area_seguridad = models.CharField(max_length=10, null=True, blank=True)
    seguimiento_area_investigaciones = models.CharField(max_length=10, null=True, blank=True)
    total_allanamientos_positivos = models.IntegerField(null=True, blank=True)
    total_allanamientos_negativos = models.IntegerField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = '"exportados"."ampliacionesinformes"'


class PersonaSGSP(models.Model):
    """Mapeo exacto de exportados.personassgsp"""
    # Usamos nro_ficha como PK porque el documento puede ser NULL o repetirse por evento
    nro_ficha = models.BigIntegerField(primary_key=True) 
    cedula = models.CharField(max_length=20, null=True, blank=True)
    nombre_completo = models.TextField(null=True, blank=True)
    edad = models.IntegerField(null=True, blank=True)
    estado_civil = models.CharField(max_length=100, null=True, blank=True)
    sexo = models.CharField(max_length=20, null=True, blank=True)
    nacionalidad = models.CharField(max_length=100, null=True, blank=True)
    alias = models.TextField(null=True, blank=True)
    fecha_nac = models.DateField(null=True, blank=True)
    ocupacion = models.TextField(null=True, blank=True)
    departamento_domicilio = models.CharField(max_length=255, null=True, blank=True)
    domicilio = models.TextField(null=True, blank=True)
    x_domicilio = models.TextField(null=True, blank=True) # Texto por la coma del SGSP
    y_domicilio = models.TextField(null=True, blank=True) # Texto por la coma del SGSP
    rol = models.CharField(max_length=255, null=True, blank=True)
    eventos_sgsp = models.BigIntegerField(null=True, blank=True)
    fecha_hecho_evento = models.DateField(null=True, blank=True)
    titulo = models.TextField(null=True, blank=True)
    complemento = models.TextField(null=True, blank=True)
    jefatura = models.CharField(max_length=255, null=True, blank=True)
    dependencia = models.CharField(max_length=255, null=True, blank=True)
    departamento_evento = models.CharField(max_length=255, null=True, blank=True)
    x_evento = models.TextField(null=True, blank=True)
    y_evento = models.TextField(null=True, blank=True)
    asociado_violencia_domestica = models.CharField(max_length=10, null=True, blank=True)
    tiene_medidas_cautelares = models.CharField(max_length=10, null=True, blank=True)
    medidas_cautelares = models.TextField(null=True, blank=True)
    espirometria = models.CharField(max_length=50, null=True, blank=True)
    test_droga_positivo = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        managed = False
        db_table = '"exportados"."personassgsp"'


# =============================================================================
# 2. VISTAS (VIEWS)
# Django las trata como tablas de solo lectura para generar los reportes.
# =============================================================================

class ViewDglccoAlias(models.Model):
    """Representa la vista exportados.v_dglcco_alias"""
    nro = models.BigIntegerField(primary_key=True)
    dependencia_alias = models.CharField(max_length=100) # La columna generada por el CASE
    titulo = models.TextField()
    ingreso = models.DateTimeField()
    aclarada = models.CharField(max_length=10)
    # Puedes mapear más campos aquí si los necesitas de la vista

    class Meta:
        managed = False
        db_table = '"exportados"."v_dglcco_alias"'


class ViewPersonaSgspDglcco(models.Model):
    """Representa la vista exportados.v_personassgsp_dglcco"""
    nro_ficha = models.BigIntegerField(primary_key=True)
    cedula = models.CharField(max_length=20)
    nombre_completo = models.TextField()
    rol = models.CharField(max_length=255)
    eventos_sgsp = models.BigIntegerField()
    # Aquí puedes añadir los campos que necesites de la vista

    class Meta:
        managed = False
        db_table = '"exportados"."v_personassgsp_dglcco"'