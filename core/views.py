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

# 2. Buscar 
def buscar_expedientes(request):
    query = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', 'persona').strip()
    
    if not query:
        return JsonResponse({'resultados': []})

    if tipo == 'persona':
        # Buscamos coincidencias en datos de la persona vinculada
        filtros = (
            Q(expedientepersona__persona__primer_nombre__icontains=query) |
            Q(expedientepersona__persona__segundo_nombre__icontains=query) |
            Q(expedientepersona__persona__primer_apellido__icontains=query) |
            Q(expedientepersona__persona__segundo_apellido__icontains=query) |
            Q(expedientepersona__persona__documento__icontains=query)
        )
    else: # expediente
        # Buscamos en el expediente propiamente dicho
        filtros = (
            Q(codigo__icontains=query) |
            Q(observaciones__icontains=query) |
            Q(oficina__nombre__icontains=query) |
            Q(oficina__codigo__icontains=query)
        )

    # Realizamos la consulta con select_related para optimizar la oficina
    expedientes = Expediente.objects.filter(filtros).select_related('oficina').distinct()

    data = []
    for exp in expedientes:
        # Obtenemos las personas vinculadas para este expediente
        vias = ExpedientePersona.objects.filter(expediente=exp).select_related('persona', 'persona__nacionalidad')
        
        if vias.exists():
            for v in vias:
                data.append({
                    'expediente_id': exp.id,
                    'expediente_codigo': exp.codigo,
                    'oficina': exp.oficina.nombre,
                    'fecha_ingreso': exp.fecha_ingreso.strftime("%d/%m/%Y"),
                    'persona_id': v.persona.id,
                    'persona_nombre': f"{v.persona.primer_nombre} {v.persona.primer_apellido}",
                    'documento': v.persona.documento,
                    'nacionalidad_cod': v.persona.nacionalidad.codigo,
                    'rol': v.get_rol_display()
                })
        else:
            # Si no tiene personas, devolvemos una fila vacía de persona pero con datos de exp
            data.append({
                'expediente_id': exp.id,
                'expediente_codigo': exp.codigo,
                'oficina': exp.oficina.nombre,
                'fecha_ingreso': exp.fecha_ingreso.strftime("%d/%m/%Y"),
                'persona_id': '',
                'persona_nombre': '--- SIN ASIGNAR ---',
                'documento': '---',
                'nacionalidad_cod': '---',
                'rol': 'N/A'
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
            # Ruta corta para Timelines (Abreviaturas)
            'ruta_corta': f"{m.origen.codigo} → {m.destino.codigo}", 
            # Ruta larga para Tabla Excel (Nombres completos)
            'ruta_larga': f"{m.origen.nombre} → {m.destino.nombre}",
            'entrega': m.entregado_por,
            'recibe': m.recibido_por,
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
        oficina_destino = Oficina.objects.get(id=data['destino_id'])
        
        # 1. Creamos el registro del movimiento
        mov = ExpedienteMovimiento.objects.create(
            expediente=exp,
            origen_id=data['origen_id'],
            destino=oficina_destino,
            fecha=data['fecha'],
            entregado_por=data['entregado_por'],
            recibido_por=data['recibido_por'],
            observaciones=data.get('observaciones')
        )

        # 2. Actualizamos la oficina actual del expediente
        exp.oficina = oficina_destino
        exp.save()

        return JsonResponse({'status': 'ok'})

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

@csrf_exempt
def vincular_persona(request, id):
    if request.method == 'POST':
        data = json.loads(request.body)
        expediente = get_object_or_404(Expediente, id=id)
        
        # 1. Obtener o crear la Persona
        # Usamos update_or_create para que si la persona ya existe, solo actualice sus nombres
        pais = Pais.objects.get(nombre=data['nacionalidad_nombre'])
        tipo_doc = TipoDocumento.objects.get(id=data['tipo_documento_id'])
        
        persona, created = Persona.objects.update_or_create(
            documento=data['documento'],
            defaults={
                'tipo_documento': tipo_doc,
                'primer_nombre': data['primer_nombre'],
                'segundo_nombre': data.get('segundo_nombre', ''),
                'primer_apellido': data['primer_apellido'],
                'segundo_apellido': data.get('segundo_apellido', ''),
                'nacionalidad': pais,
            }
        )

        # 2. Crear el vínculo en ExpedientePersona
        ExpedientePersona.objects.get_or_create(
            expediente=expediente,
            persona=persona,
            defaults={'rol': data['rol'].lower()}
        )

        return JsonResponse({'status': 'ok'})