from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.db.models.functions import Concat
from django.db.models import Value
import json
from .models import *

# 1. Vista para renderizar la página principal
def home(request):
    return render(request, 'core/home.html')

# 2. Buscar Expedientes (Devuelve JSON)
def buscar_expedientes(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'resultados': []})

    # Iniciamos desde Expediente para asegurar que aparezcan los que no tienen personas
    # Usamos values para obtener los datos de la relación (Left Join automático)
    resultados_raw = Expediente.objects.filter(
        Q(codigo__icontains=query) | 
        Q(observaciones__icontains=query) |
        Q(expedientepersona__persona__primer_nombre__icontains=query) |
        Q(expedientepersona__persona__primer_apellido__icontains=query) |
        Q(expedientepersona__persona__documento__icontains=query)
    ).annotate(
        # Traemos los datos de la persona vinculada (si existen)
        p_id=models.F('expedientepersona__persona__id'),
        p_nom=Concat(
            'expedientepersona__persona__primer_nombre', Value(' '), 
            'expedientepersona__persona__primer_apellido'
        ),
        p_doc=models.F('expedientepersona__persona__documento'),
        p_pais=models.F('expedientepersona__persona__nacionalidad__codigo'), # <--- CÓDIGO DE PAÍS
        p_rol=models.F('expedientepersona__rol')
    ).values(
        'id', 'codigo', 'oficina__nombre', 'fecha_ingreso',
        'p_id', 'p_nom', 'p_doc', 'p_pais', 'p_rol'
    ).distinct()

    data = []
    for r in resultados_raw:
        data.append({
            'expediente_id': r['id'],
            'expediente_codigo': r['codigo'],
            'oficina': r['oficina__nombre'],
            'fecha_ingreso': r['fecha_ingreso'].strftime("%d/%m/%Y"),
            # Si p_id es None, significa que el expediente está vacío
            'persona_id': r['p_id'] or '',
            'persona_nombre': r['p_nom'] or '--- SIN ASIGNAR ---',
            'documento': r['p_doc'] or '---',
            'nacionalidad_cod': r['p_pais'] or '---', # Mostramos el Código (ej: URY)
            'rol': r['p_rol'] or 'N/A'
        })
        
    return JsonResponse({'resultados': data})

# 3. Obtener detalles completos de un expediente
def detalle_expediente(request, id):
    exp = get_object_or_404(Expediente, id=id)
    
    # Personas vinculadas
    personas_vinculadas = ExpedientePersona.objects.filter(expediente=exp).select_related('persona', 'persona__nacionalidad')
    lista_personas = []
    for vp in personas_vinculadas:
        lista_personas.append({
            'primer_nombre': vp.persona.primer_nombre,
            'segundo_nombre': vp.persona.segundo_nombre or '',
            'primer_apellido': vp.persona.primer_apellido,
            'segundo_apellido': vp.persona.segundo_apellido or '',
            'documento': vp.persona.documento,
            'nacionalidad_nombre': vp.persona.nacionalidad.nombre, # Nombre del país
            'rol': vp.get_rol_display() # Texto legible: "Indagado", "Víctima", etc.
        })

    # Movimientos del expediente
    movimientos = ExpedienteMovimiento.objects.filter(expediente=exp).order_by('-fecha')
    lista_movs = []
    for m in movimientos:
        lista_movs.append({
            'fecha': m.fecha.strftime("%d/%m/%Y %H:%M"),
            'tipo': m.tipo_movimiento.nombre,
            'obs': m.observaciones
        })

    return JsonResponse({
        'id': exp.id,
        'codigo': exp.codigo,
        'observaciones': exp.observaciones,
        'subido_alfresco': exp.subido_alfresco,
        'personas': lista_personas,
        'movimientos': lista_movs
    })

# 4. Actualizar estado Alfresco (POST)
@csrf_exempt # Solo si no manejas el token CSRF en Vue todavía
def actualizar_alfresco(request, id):
    if request.method == 'POST':
        exp = get_object_or_404(Expediente, id=id)
        data = json.loads(request.body)
        exp.subido_alfresco = data.get('estado', False)
        exp.save()
        return JsonResponse({'status': 'ok'})

# 5. Crear Expediente (POST)
@csrf_exempt
def crear_expediente(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        oficina = Oficina.objects.get(id=data['oficina_id'])
        nuevo_exp = Expediente.objects.create(
            codigo=data['codigo'],
            fecha_ingreso=data['fecha'],
            oficina=oficina,
            observaciones=data.get('observaciones', ''),
            created_by=request.user if request.user.is_authenticated else None
        )
        return JsonResponse({'status': 'ok', 'id': nuevo_exp.id})
    
# 5.1. Función para recuperar los últimos 10 registros de expedientes
def expedientes_recientes(request):
    # Obtenemos los últimos 10 expedientes creados
    recientes = Expediente.objects.all().order_by('-id')[:10]
    data = []
    for exp in recientes:
        data.append({
            'id': exp.id,
            'codigo': exp.codigo,
            'fecha_ingreso': exp.fecha_ingreso.strftime("%d/%m/%Y"),
            # Truncamos las observaciones para que no rompan la tabla si son muy largas
            'observaciones': (exp.observaciones[:75] + '...') if exp.observaciones and len(exp.observaciones) > 75 else (exp.observaciones or '')
        })
    return JsonResponse({'recientes': data})
    
# 6. Oficinas
def lista_oficinas(request):
    oficinas = Oficina.objects.all().values('id', 'nombre')
    return JsonResponse({'oficinas': list(oficinas)})

#7 Países
def lista_paises(request):
    paises = Pais.objects.all().order_by('nombre').values('id', 'nombre')
    return JsonResponse({'paises': list(paises)})

# Tipo de documento (si es cedula pasaporte o que)
def lista_tipos_documento(request):
    tipos = TipoDocumento.objects.all().values('id', 'nombre')
    return JsonResponse({'tipos': list(tipos)})