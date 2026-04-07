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
from django.db.models.functions import Concat
from django.db.models import Value

def buscar_expedientes(request):
    query = request.GET.get('q', '').strip()
    
    if not query:
        return JsonResponse({'resultados': []})

    # Buscamos en la tabla intermedia ExpedientePersona
    # Esto nos permite devolver una fila por cada persona en cada expediente
    vinculos = ExpedientePersona.objects.select_related('persona', 'expediente', 'expediente__oficina', 'persona__nacionalidad').annotate(
        nombre_completo=Concat(
            'persona__primer_nombre', Value(' '), 'persona__primer_apellido'
        )
    ).filter(
        Q(expediente__codigo__icontains=query) | 
        Q(persona__documento__icontains=query) |
        Q(nombre_completo__icontains=query)
    ).distinct()
    
    data = []
    for v in vinculos:
        data.append({
            'persona_id': v.persona.id,
            'persona_nombre': f"{v.persona.primer_nombre} {v.persona.primer_apellido}",
            'documento': v.persona.documento,
            'nacionalidad': v.persona.nacionalidad.nombre,
            'rol': v.get_rol_display(), # 'Imputado', 'Víctima', etc.
            'expediente_id': v.expediente.id,
            'expediente_codigo': v.expediente.codigo,
            'oficina': v.expediente.oficina.nombre,
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