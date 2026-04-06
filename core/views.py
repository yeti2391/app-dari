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

    # Usamos Concat para crear un campo virtual que una Nombre + Espacio + Apellido
    # Esto permite buscar "Mario Ferreira" completo
    expedientes = Expediente.objects.annotate(
        nombre_completo=Concat(
            'expedientepersona__persona__primer_nombre', 
            Value(' '), 
            'expedientepersona__persona__primer_apellido'
        )
    ).filter(
        Q(codigo__icontains=query) | 
        Q(observaciones__icontains=query) |
        Q(nombre_completo__icontains=query) | # Busca en el nombre unido
        Q(expedientepersona__persona__documento__icontains=query) |
        Q(expedientepersona__persona__primer_nombre__icontains=query) |
        Q(expedientepersona__persona__primer_apellido__icontains=query)
    ).select_related('oficina').distinct()
    
    data = []
    for exp in expedientes:
        data.append({
            'id': exp.id,
            'codigo': exp.codigo,
            'oficina': exp.oficina.nombre,
            'fecha_ingreso': exp.fecha_ingreso.strftime("%d/%m/%Y"),
            'subido_alfresco': exp.subido_alfresco
        })
        
    return JsonResponse({'resultados': data})

# 3. Obtener detalles completos de UN expediente
def detalle_expediente(request, id):
    exp = get_object_or_404(Expediente, id=id)
    
    # Personas vinculadas
    personas_vinculadas = ExpedientePersona.objects.filter(expediente=exp).select_related('persona', 'persona__nacionalidad')
    lista_personas = []
    for vp in personas_vinculadas:
        lista_personas.append({
            'nombre': f"{vp.persona.primer_nombre} {vp.persona.primer_apellido}",
            'documento': vp.persona.documento,
            'nacionalidad': vp.persona.nacionalidad.nombre,
            'rol': vp.get_rol_display()
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
    
# 6. Oficinas
def lista_oficinas(request):
    oficinas = Oficina.objects.all().values('id', 'nombre')
    return JsonResponse({'oficinas': list(oficinas)})