from django.db import models
from django.contrib.auth.models import User
from core.models import Persona, Identificacion, Pais, TipoDocumento
from datetime import date

class DepartamentoUru(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.nombre

class DependenciaPolicial(models.Model):
    departamento = models.ForeignKey(DepartamentoUru, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=150)
    def __str__(self): return f"{self.departamento.nombre} - {self.nombre}"

class FichaAusente(models.Model):
    # --- VÍNCULO ÚNICO CON PERSONA ---
    persona = models.ForeignKey(Persona, on_delete=models.PROTECT, related_name='fichas_ausencia')
    
    # --- DATOS ESPECÍFICOS DE LA AUSENCIA ---
    equipo = models.CharField(max_length=20, blank=True, null=True)
    nro_caso = models.CharField(max_length=20, unique=True)
    biblio = models.CharField(max_length=255, blank=True, null=True)
    
    # Datos que pueden variar en cada ausencia (ej. la edad cambia con el tiempo)
    edad_al_momento = models.IntegerField(editable=False, null=True)
    franja_etaria = models.CharField(max_length=50, editable=False, null=True)
    genero = models.CharField(max_length=20, choices=[('MASCULINO','Masculino'),('FEMENINO','Femenino'),('DIVERSO','Diverso')])

    # Ubicación y SGSP
    departamento_hecho = models.ForeignKey(DepartamentoUru, on_delete=models.PROTECT)
    dependencia = models.ForeignKey(DependenciaPolicial, on_delete=models.PROTECT)
    lugar_ausencia = models.CharField(max_length=100) # Domicilio, etc.
    
    nro_sgsp = models.BigIntegerField(db_index=True)
    tipificacion = models.CharField(max_length=100)
    fecha_hecho = models.DateTimeField()
    fecha_ingreso_sgsp = models.DateTimeField()

    # Checks
    divulgacion = models.BooleanField(default=False)
    inau = models.BooleanField(default=False)
    adn = models.BooleanField(default=False)
    bps = models.BooleanField(default=False)
    factores_riesgo = models.TextField(blank=True, null=True)

    # Estado
    fecha_ubicacion = models.DateField(null=True, blank=True)
    estado_persona = models.CharField(max_length=20, blank=True, null=True)
    estado_investigacion = models.CharField(max_length=20, default='ABIERTA')

    # Auditoría
    ingresado_por = models.ForeignKey(User, on_delete=models.PROTECT)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Calcular edad basada en la fecha_nacimiento de la Persona vinculada
        if self.persona.fecha_nacimiento:
            f_nac = self.persona.fecha_nacimiento
            today = date.today()
            self.edad_al_momento = today.year - f_nac.year - ((today.month, today.day) < (f_nac.month, f_nac.day))
            
            if self.edad_al_momento <= 11: self.franja_etaria = 'NIÑO/A'
            elif self.edad_al_momento <= 17: self.franja_etaria = 'ADOLESCENTE'
            elif self.edad_al_momento < 65: self.franja_etaria = 'ADULTO'
            else: self.franja_etaria = 'ADULTO MAYOR'
        super().save(*args, **kwargs)

class HistorialFicha(models.Model):
    ficha = models.ForeignKey(FichaAusente, on_delete=models.CASCADE, related_name='historial')
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    fecha = models.DateTimeField(auto_now_add=True)
    accion = models.CharField(max_length=100)
    observaciones = models.TextField()