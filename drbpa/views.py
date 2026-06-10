from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.views.decorators.csrf import csrf_exempt
from datetime import date
import json

# Importamos los modelos de ambas apps
from .models import DepartamentoUru, DependenciaPolicial, FichaAusente, HistorialFicha
from core.models import Pais, TipoDocumento, Persona, Identificacion

# =============================================================================
# SEGURIDAD Y PERMISOS
# =============================================================================

def es_drbpa(user):
    """Verifica si el usuario pertenece al grupo DRBPA o es superusuario."""
    if user.groups.filter(name='DRBPA').exists() or user.is_superuser:
        return True
    raise PermissionDenied

# =============================================================================
# VISTAS DE NAVEGACIÓN
# =============================================================================

@login_required
@user_passes_test(es_drbpa)
def drbpa_home(request):
    """Renderiza la interfaz principal del departamento (los botones de menú)."""
    return render(request, 'drbpa/drbpa.html')

@login_required
@user_passes_test(es_drbpa)
def nuevo_registro(request):
    """Renderiza el formulario de alta de nueva persona ausente."""
    return render(request, 'drbpa/nuevo_registro.html')

# =============================================================================
# API DE DATOS MAESTROS (PARA FORMULARIOS)
# =============================================================================

@login_required
@user_passes_test(es_drbpa)
def api_maestros_drbpa(request):
    """Envía todas las listas necesarias (Uruguay, Países, Docs) para Vue."""
    paises = list(Pais.objects.all().order_by('nombre').values('id', 'nombre'))
    tipos_doc = list(TipoDocumento.objects.all().values('id', 'nombre'))
    deptos = list(DepartamentoUru.objects.all().order_by('nombre').values('id', 'nombre'))
    # Traemos las dependencias con el ID de su departamento para filtrar en Vue
    deps = list(DependenciaPolicial.objects.all().order_by('nombre').values('id', 'nombre', 'departamento_id'))
    
    return JsonResponse({
        'paises': paises,
        'tipos_doc': tipos_doc,
        'departamentos': deptos,
        'dependencias': deps
    })

# =============================================================================
# LÓGICA DE GUARDADO Y AUDITORÍA
# =============================================================================

@login_required
@user_passes_test(es_drbpa)
@csrf_exempt
def api_guardar_ficha(request):
    """Procesa el formulario, crea/busca la persona y genera el rastro de historial."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user = request.user

            # 1. LÓGICA DE IDENTIDAD (Similar a core/views.py)
            # Buscamos si la persona ya existe por su documento
            ident = Identificacion.objects.filter(
                numero=data['documento'].strip().upper(),
                tipo_documento_id=data['tipo_doc_id']
            ).first()

            if ident:
                persona = ident.persona
            else:
                # Si no existe, buscamos el país (default Uruguay si no hay nombre)
                pais_nombre = data.get('pais_nombre', 'URUGUAY')
                pais = Pais.objects.filter(nombre__iexact=pais_nombre).first()
                if not pais: pais = Pais.objects.get(id=249) # OTRO

                persona = Persona.objects.create(
                    primer_nombre=data.get('p_nombre'),
                    segundo_nombre=data.get('s_nombre'),
                    primer_apellido=data.get('p_apellido'),
                    segundo_apellido=data.get('s_apellido'),
                    fecha_nacimiento=data.get('fecha_nac') or None,
                    nacionalidad=pais,
                    created_by=user
                )
                Identificacion.objects.create(
                    persona=persona, 
                    tipo_documento_id=data['tipo_doc_id'], 
                    numero=data['documento'].strip().upper()
                )

            # 2. GENERACIÓN AUTOMÁTICA DEL NRO_CASO (Ej: 2026/701)
            anio_actual = date.today().year
            # Buscamos el último caso del año actual
            ultimo = FichaAusente.objects.filter(nro_caso__startswith=str(anio_actual)).order_by('-id').first()
            if ultimo:
                # Si existe, extraemos el número después de la barra y sumamos 1
                nro_serial = int(ultimo.nro_caso.split('/')[1]) + 1
            else:
                nro_serial = 1 # Primer caso del año
            
            nuevo_nro_caso = f"{anio_actual}/{str(nro_serial).zfill(2)}"

            # 3. CREACIÓN DE LA FICHA DE AUSENCIA
            ficha = FichaAusente.objects.create(
                persona=persona,
                equipo=data.get('equipo'),
                nro_caso=nuevo_nro_caso,
                genero=data.get('genero'),
                departamento_hecho_id=data.get('depto_id'),
                dependencia_id=data.get('dep_id'),
                lugar_ausencia=data.get('lugar'),
                nro_sgsp=data.get('nro_sgsp'),
                tipificacion=data.get('tipificacion'),
                fecha_hecho=data.get('f_hecho'),
                fecha_ingreso_sgsp=data.get('f_ingreso_sgsp'),
                ingresado_por=user
            )

            # 4. HISTORIAL AUTOMÁTICO (Auditoría)
            HistorialFicha.objects.create(
                ficha=ficha,
                usuario=user,
                accion="CREACIÓN",
                observaciones=f"Registro inicial del caso {nuevo_nro_caso}."
            )

            return JsonResponse({'status': 'ok', 'nro_caso': nuevo_nro_caso})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error'}, status=405)