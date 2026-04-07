from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, F, Value
from django.db.models.functions import Concat
import json
from .models import *

# 1. Vista principal
def home(request):
    return render(request, 'core/home.html')

# 2. Buscar (Universal)
def buscar_expedientes(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'resultados': []})

    resultados_raw = Expediente.objects.filter(
        Q(codigo__icontains=query) | 
        Q(observaciones__icontains=query) |
        Q(expedientepersona__persona__primer_nombre__icontains=query) |
        Q(expedientepersona__persona__primer_apellido__icontains=query) |
        Q(expedientepersona__persona__documento__icontains=query)
    ).annotate(
        p_id=F('expedientepersona__persona__id'),
        p_nom=Concat('expedientepersona__persona__primer_nombre', Value(' '), 'expedientepersona__persona__primer_apellido'),
        p_doc=F('expedientepersona__persona__documento'),
        p_pais=F('expedientepersona__persona__nacionalidad__codigo'),
        p_rol=F('expedientepersona__rol')
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
            'persona_id': r['p_id'] or '',
            'persona_nombre': r['p_nom'] or '--- SIN ASIGNAR ---',
            'documento': r['p_doc'] or '---',
            'nacionalidad_cod': r['p_pais'] or '---',
            'rol': r['p_rol'] or 'N/A'
        })
    return JsonResponse({'resultados': data})

# 3. Detalles del expediente
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
            'nacionalidad_nombre': vp.persona.nacionalidad.nombre,
            'rol': vp.get_rol_display()
        })

    # Movimientos para el Timeline de detalles
    movs = ExpedienteMovimiento.objects.filter(expediente=exp).select_related('origen', 'destino').order_by('-fecha')
    lista_movs = []
    for m in movs:
        lista_movs.append({
            'fecha': m.fecha.strftime("%d/%m/%Y %H:%M"),
            'tipo': f"{m.origen.nombre} -> {m.destino.nombre}", # Resumen para el timeline
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

# --- VISTAS DE MOVIMIENTOS (EXTERNAS) ---

def lista_tipos_movimiento(request):
    tipos = TipoMovimiento.objects.all().values('id', 'nombre')
    return JsonResponse({'tipos': list(tipos)})

@csrf_exempt
def registrar_movimiento(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        exp = get_object_or_404(Expediente, codigo=data['codigo_expediente'])
        mov = ExpedienteMovimiento.objects.create(
            expediente=exp,
            origen_id=data['origen_id'],
            destino_id=data['destino_id'],
            fecha=data['fecha'],
            entregado_por=data['entregado_por'],
            recibido_por=data['recibido_por'],
            observaciones=data.get('observaciones')
        )
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)

def historial_movimientos(request):
    codigo = request.GET.get('codigo')
    movs = ExpedienteMovimiento.objects.filter(expediente__codigo=codigo).select_related('origen', 'destino').order_by('-fecha')
    data = []
    for m in movs:
        data.append({
            'fecha': m.fecha.strftime("%d/%m/%Y %H:%M"),
            'origen': m.origen.nombre,
            'destino': m.destino.nombre,
            'entrega': m.entregado_por,
            'recibe': m.recibido_por,
            'obs': m.observaciones
        })
    return JsonResponse({'historial': data})

# --- OTRAS VISTAS ---

@csrf_exempt
def actualizar_alfresco(request, id):
    if request.method == 'POST':
        exp = get_object_or_404(Expediente, id=id)
        data = json.loads(request.body)
        exp.subido_alfresco = data.get('estado', False)
        exp.save()
        return JsonResponse({'status': 'ok'})

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
        )
        return JsonResponse({'status': 'ok', 'id': nuevo_exp.id})

def expedientes_recientes(request):
    recientes = Expediente.objects.all().order_by('-id')[:10]
    data = []
    for exp in recientes:
        data.append({
            'id': exp.id,
            'codigo': exp.codigo,
            'fecha_ingreso': exp.fecha_ingreso.strftime("%d/%m/%Y"),
            'observaciones': (exp.observaciones[:75] + '...') if exp.observaciones and len(exp.observaciones) > 75 else (exp.observaciones or '')
        })
    return JsonResponse({'recientes': data})

def lista_oficinas(request):
    oficinas = Oficina.objects.all().values('id', 'nombre')
    return JsonResponse({'oficinas': list(oficinas)})

def lista_paises(request):
    paises = Pais.objects.all().order_by('nombre').values('id', 'nombre')
    return JsonResponse({'paises': list(paises)})

def lista_tipos_documento(request):
    tipos = TipoDocumento.objects.all().values('id', 'nombre')
    return JsonResponse({'tipos': list(tipos)})