from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, F, Value, CharField
from django.db.models.functions import Concat
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
import json
from .models import *

# =============================================================================
# 1. FUNCIONES DE APOYO Y PERMISOS
# =============================================================================

def es_personal_autorizado(user):
    """Verifica si el usuario pertenece a DARI, DRBPA o es Superusuario."""
    grupos_permitidos = ['DARI', 'DRBPA']
    if user.groups.filter(name__in=grupos_permitidos).exists() or user.is_superuser:
        return True
    raise PermissionDenied

def clean_val(val):
    """Convierte cadenas vacías en None (NULL en DB)."""
    if val is None: return None
    text = str(val).strip()
    return text if text != "" else None

def get_pais_default(nombre_buscado=None):
    """Busca país por nombre; si falla, devuelve el ID 249 (OTRO)."""
    pais = None
    if nombre_buscado:
        pais = Pais.objects.filter(nombre__iexact=nombre_buscado.strip()).first()
    if not pais:
        pais = Pais.objects.filter(id=249).first()
    return pais

# =============================================================================
# 2. VISTAS DE NAVEGACIÓN
# =============================================================================

@login_required
@user_passes_test(es_personal_autorizado)
def home(request):
    """Renderiza la interfaz principal."""
    return render(request, 'core/home.html')

# =============================================================================
# 3. MOTOR DE BÚSQUEDA HÍBRIDO
# =============================================================================

@login_required
@user_passes_test(es_personal_autorizado)
def buscar_expedientes(request):
    """Buscador avanzado Persona/Expediente."""
    query_general = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', 'persona').strip()
    mode = request.GET.get('mode', 'quick').strip()
    
    n1, n2, a1, a2, doc, alias = [request.GET.get(x, '').strip() for x in ['n1', 'n2', 'a1', 'a2', 'doc', 'alias']]

    if not any([query_general, n1, n2, a1, a2, doc, alias]):
        return JsonResponse({'resultados': []})

    data = []

    if tipo == 'persona':
        vinculos = ExpedientePersona.objects.select_related(
            'persona', 'expediente', 'expediente__oficina', 'persona__nacionalidad'
        ).prefetch_related('persona__identificaciones__tipo_documento', 'persona__aliases')

        if mode == 'advanced':
            filtros = Q()
            if n1: filtros &= Q(persona__primer_nombre__icontains=n1)
            if n2: filtros &= Q(persona__segundo_nombre__icontains=n2)
            if a1: filtros &= Q(persona__primer_apellido__icontains=a1)
            if a2: filtros &= Q(persona__segundo_apellido__icontains=a2)
            if doc: filtros &= Q(persona__identificaciones__numero__icontains=doc)
            if alias: filtros &= Q(persona__aliases__alias__icontains=alias)
            vinculos = vinculos.filter(filtros)
        else:
            vinculos = vinculos.annotate(
                full_name=Concat(
                    'persona__primer_nombre', Value(' '), 'persona__segundo_nombre', Value(' '),
                    'persona__primer_apellido', Value(' '), 'persona__segundo_apellido',
                    output_field=CharField()
                )
            ).filter(
                Q(full_name__icontains=query_general) |
                Q(persona__identificaciones__numero__icontains=query_general) |
                Q(persona__aliases__alias__icontains=query_general)
            )

        for v in vinculos.distinct():
            docs = v.persona.identificaciones.all()
            data.append({
                'expediente_id': v.expediente.id,
                'expediente_codigo': v.expediente.codigo,
                'oficina': v.expediente.oficina.nombre,
                'fecha_ingreso': v.expediente.fecha_ingreso.strftime("%d/%m/%Y"),
                'persona_id': v.persona.id,
                'persona_nombre': f"{v.persona.primer_nombre or ''} {v.persona.segundo_nombre or ''} {v.persona.primer_apellido or ''} {v.persona.segundo_apellido or ''}".strip(),
                'persona_aliases': ", ".join([a.alias for a in v.persona.aliases.all()]),
                'documento': ", ".join([f"{d.tipo_documento.nombre}: {d.numero}" for d in docs]) if docs else "---",
                'nacionalidad_cod': v.persona.nacionalidad.codigo_alpha3 if v.persona.nacionalidad else '---',
                'rol': v.get_rol_display(),
                # Datos para autocompletado
                'primer_nombre': v.persona.primer_nombre or '',
                'segundo_nombre': v.persona.segundo_nombre or '',
                'primer_apellido': v.persona.primer_apellido or '',
                'segundo_apellido': v.persona.segundo_apellido or '',
                'fecha_nacimiento_iso': v.persona.fecha_nacimiento.strftime("%Y-%m-%d") if v.persona.fecha_nacimiento else '',
                'nacionalidad_nombre': v.persona.nacionalidad.nombre if v.persona.nacionalidad else ''
            })

    else: # Búsqueda EXPEDIENTE
        query_norm = query_general.upper()
        expedientes = Expediente.objects.filter(
            Q(codigo__icontains=query_norm) | Q(observaciones__icontains=query_general) | Q(oficina__nombre__icontains=query_general)
        ).select_related('oficina').distinct()

        for exp in expedientes:
            vias = ExpedientePersona.objects.filter(expediente=exp).select_related('persona', 'persona__nacionalidad').prefetch_related('persona__identificaciones__tipo_documento', 'persona__aliases')
            if vias.exists():
                for v in vias:
                    data.append({
                        'expediente_id': exp.id, 'expediente_codigo': exp.codigo, 'oficina': exp.oficina.nombre,
                        'fecha_ingreso': exp.fecha_ingreso.strftime("%d/%m/%Y"), 'persona_id': v.persona.id,
                        'persona_nombre': f"{v.persona.primer_nombre or ''} {v.persona.primer_apellido or ''}".strip(),
                        'documento': ", ".join([f"{d.tipo_documento.nombre}: {d.numero}" for d in v.persona.identificaciones.all()]) or "---",
                        'nacionalidad_cod': v.persona.nacionalidad.codigo_alpha3 if v.persona.nacionalidad else '---',
                        'rol': v.get_rol_display()
                    })
            else:
                data.append({
                    'expediente_id': exp.id, 'expediente_codigo': exp.codigo, 'oficina': exp.oficina.nombre,
                    'fecha_ingreso': exp.fecha_ingreso.strftime("%d/%m/%Y"), 'persona_id': '',
                    'persona_nombre': '--- SIN ASIGNAR ---', 'documento': '---', 'nacionalidad_cod': '---', 'rol': 'N/A'
                })
    return JsonResponse({'resultados': data})

# =============================================================================
# 4. GESTIÓN DE DETALLES
# =============================================================================

@login_required
@user_passes_test(es_personal_autorizado)
def detalle_expediente(request, id):
    exp = get_object_or_404(Expediente, id=id)
    vinculos = ExpedientePersona.objects.filter(expediente=exp).select_related('persona', 'persona__nacionalidad').prefetch_related('persona__identificaciones__tipo_documento', 'persona__aliases')
    
    lista_personas = []
    for vp in vinculos:
        lista_personas.append({
            'persona_id': vp.persona.id,
            'primer_nombre': vp.persona.primer_nombre or '',
            'segundo_nombre': vp.persona.segundo_nombre or '',
            'primer_apellido': vp.persona.primer_apellido or '',
            'segundo_apellido': vp.persona.segundo_apellido or '',
            'documento': ", ".join([f"{d.tipo_documento.nombre}: {d.numero}" for d in vp.persona.identificaciones.all()]) or "---",
            'nacionalidad_nombre': vp.persona.nacionalidad.nombre if vp.persona.nacionalidad else 'N/A',
            'rol': vp.get_rol_display(),
            'persona_aliases': ", ".join([a.alias for a in vp.persona.aliases.all()])
        })

    movs = ExpedienteMovimiento.objects.filter(expediente=exp).select_related('origen', 'destino').order_by('-fecha')
    lista_movs = [{'fecha': m.fecha.strftime("%d/%m/%Y %H:%M"), 'ruta_corta': f"{m.origen.codigo} → {m.destino.codigo}", 'ruta_larga': f"{m.origen.nombre} → {m.destino.nombre}", 'entrega': m.entregado_por, 'recibe': m.recibido_por, 'obs': m.observaciones} for m in movs]

    return JsonResponse({'id': exp.id, 'codigo': exp.codigo, 'observaciones': exp.observaciones, 'subido_alfresco': exp.subido_alfresco, 'personas': lista_personas, 'movimientos': lista_movs, 'oficina_id': exp.oficina.id})

@login_required
@user_passes_test(es_personal_autorizado)
def detalle_persona(request, id):
    persona = get_object_or_404(Persona, id=id)
    identificaciones = [{'id': i.id, 'tipo': i.tipo_documento.nombre, 'numero': i.numero} for i in persona.identificaciones.all().select_related('tipo_documento')]
    expedientes = [{'id': v.expediente.id, 'codigo': v.expediente.codigo, 'oficina': v.expediente.oficina.nombre, 'rol': v.get_rol_display()} for v in ExpedientePersona.objects.filter(persona=persona).select_related('expediente__oficina')]

    return JsonResponse({
        'id': persona.id, 'primer_nombre': persona.primer_nombre or '', 'segundo_nombre': persona.segundo_nombre or '', 'primer_apellido': persona.primer_apellido or '', 'segundo_apellido': persona.segundo_apellido or '',
        'fecha_nacimiento': persona.fecha_nacimiento.strftime("%d/%m/%Y") if persona.fecha_nacimiento else None,
        'fecha_nacimiento_iso': persona.fecha_nacimiento.strftime("%Y-%m-%d") if persona.fecha_nacimiento else '',
        'nacionalidad': persona.nacionalidad.nombre if persona.nacionalidad else 'N/A',
        'identificaciones': identificaciones, 'aliases': [a.alias for a in persona.aliases.all()], 'expedientes': expedientes
    })

# =============================================================================
# 5. ACCIONES (POST)
# =============================================================================

@login_required
@user_passes_test(es_personal_autorizado)
@csrf_exempt
def crear_expediente(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        codigo = data['codigo'].upper().strip()
        if Expediente.objects.filter(codigo__iexact=codigo).exists():
            return JsonResponse({'status': 'error', 'message': 'El expediente ya existe.'}, status=400)
        nuevo_exp = Expediente.objects.create(codigo=codigo, fecha_ingreso=data['fecha'], oficina_id=data['oficina_id'], observaciones=data.get('observaciones', ''), created_by=request.user)
        return JsonResponse({'status': 'ok', 'id': nuevo_exp.id})

@login_required
@user_passes_test(es_personal_autorizado)
@csrf_exempt
def vincular_persona(request, id):
    if request.method == 'POST':
        data = json.loads(request.body)
        expediente = get_object_or_404(Expediente, id=id)
        p_nom1, p_nom2, p_ape1, p_ape2, f_nac = [clean_val(data.get(x)) for x in ['primer_nombre', 'segundo_nombre', 'primer_apellido', 'segundo_apellido', 'fecha_nacimiento']]
        doc_num = data.get('documento', '').strip().upper()
        
        persona = None
        if doc_num and data.get('tipo_documento_id'):
            ident = Identificacion.objects.filter(numero=doc_num, tipo_documento_id=data['tipo_documento_id']).first()
            if ident: persona = ident.persona

        if not persona:
            persona = Persona.objects.create(primer_nombre=p_nom1, segundo_nombre=p_nom2, primer_apellido=p_ape1, segundo_apellido=p_ape2, fecha_nacimiento=f_nac, nacionalidad=get_pais_default(data.get('nacionalidad_nombre')), created_by=request.user)
            if doc_num and data.get('tipo_documento_id'):
                Identificacion.objects.create(persona=persona, tipo_documento_id=data['tipo_documento_id'], numero=doc_num)
        else:
            persona.segundo_nombre = p_nom2; persona.segundo_apellido = p_ape2; persona.save()

        ExpedientePersona.objects.get_or_create(expediente=expediente, persona=persona, defaults={'rol': data.get('rol', 'indagado').lower()})
        if data.get('alias'):
            for a in data['alias'].split(','):
                name = a.strip().upper()
                if name: Alias.objects.get_or_create(persona=persona, alias=name)
        return JsonResponse({'status': 'ok', 'persona_id': persona.id})

@login_required
@user_passes_test(es_personal_autorizado)
@csrf_exempt
def actualizar_biografia_persona(request, id):
    if request.method == 'POST':
        data = json.loads(request.body)
        persona = get_object_or_404(Persona, id=id)
        persona.primer_nombre = data.get('primer_nombre', ''); persona.segundo_nombre = data.get('segundo_nombre', '')
        persona.primer_apellido = data.get('primer_apellido', ''); persona.segundo_apellido = data.get('segundo_apellido', '')
        persona.fecha_nacimiento = data.get('fecha_nacimiento') or None
        persona.nacionalidad = get_pais_default(data.get('nacionalidad_nombre'))
        persona.save()
        return JsonResponse({'status': 'ok'})

@login_required
@user_passes_test(es_personal_autorizado)
@csrf_exempt
def registrar_movimiento(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        exp = get_object_or_404(Expediente, codigo=data['codigo_expediente'])
        dest = get_object_or_404(Oficina, id=data['destino_id'])
        ExpedienteMovimiento.objects.create(expediente=exp, origen_id=data['origen_id'], destino=dest, fecha=data['fecha'], entregado_por=data['entregado_por'], recibido_por=data['recibido_por'], observaciones=data.get('observaciones'))
        exp.oficina = dest; exp.save()
        return JsonResponse({'status': 'ok'})

@login_required
@user_passes_test(es_personal_autorizado)
@csrf_exempt
def agregar_identificacion_persona(request, id):
    if request.method == 'POST':
        data = json.loads(request.body)
        num = data['numero'].upper().strip()
        if not Identificacion.objects.filter(tipo_documento_id=data['tipo_documento_id'], numero=num).exists():
            Identificacion.objects.create(persona_id=id, tipo_documento_id=data['tipo_documento_id'], numero=num)
            return JsonResponse({'status': 'ok'})
        return JsonResponse({'status': 'error', 'message': 'Documento ya registrado.'}, status=400)

@login_required
@user_passes_test(es_personal_autorizado)
@csrf_exempt
def agregar_alias_persona(request, id):
    if request.method == 'POST':
        data = json.loads(request.body)
        Alias.objects.get_or_create(persona_id=id, alias=data.get('alias', '').strip().upper())
        return JsonResponse({'status': 'ok'})

@login_required
@user_passes_test(es_personal_autorizado)
@csrf_exempt
def desvincular_persona(request, id):
    if request.method == 'POST':
        data = json.loads(request.body)
        ExpedientePersona.objects.filter(expediente_id=id, persona_id=data.get('persona_id')).delete()
        return JsonResponse({'status': 'ok'})

@login_required
@user_passes_test(es_personal_autorizado)
@csrf_exempt
def vincular_persona_existente(request, id):
    if request.method == 'POST':
        data = json.loads(request.body)
        ExpedientePersona.objects.get_or_create(expediente_id=id, persona_id=data['persona_id'], defaults={'rol': data.get('rol', 'indagado').lower()})
        return JsonResponse({'status': 'ok'})

@login_required
@user_passes_test(es_personal_autorizado)
@csrf_exempt
def actualizar_alfresco(request, id):
    if request.method == 'POST':
        exp = get_object_or_404(Expediente, id=id)
        data = json.loads(request.body)
        exp.subido_alfresco = data.get('estado', False)
        exp.save()
        return JsonResponse({'status': 'ok'})

@login_required
@user_passes_test(es_personal_autorizado)
@csrf_exempt
def actualizar_obs_expediente(request, id):
    if request.method == 'POST':
        data = json.loads(request.body)
        exp = get_object_or_404(Expediente, id=id)
        exp.observaciones = data.get('observaciones', '')
        exp.save()
        return JsonResponse({'status': 'ok'})

# =============================================================================
# 6. VISTAS DE SOPORTE (LISTAS Y RECIENTES)
# =============================================================================

def lista_oficinas(request):
    return JsonResponse({'oficinas': list(Oficina.objects.all().order_by('nombre').values('id', 'nombre', 'activa'))})

def lista_paises(request):
    return JsonResponse({'paises': list(Pais.objects.all().order_by('nombre').values('id', 'nombre'))})

def lista_tipos_documento(request):
    return JsonResponse({'tipos': list(TipoDocumento.objects.all().values('id', 'nombre'))})

@login_required
@user_passes_test(es_personal_autorizado)
def historial_movimientos(request):
    codigo = request.GET.get('codigo')
    movs = ExpedienteMovimiento.objects.filter(expediente__codigo=codigo).select_related('origen', 'destino').order_by('-fecha')
    data = [{'fecha': m.fecha.strftime("%d/%m/%Y %H:%M"), 'origen': m.origen.nombre, 'destino': m.destino.nombre, 'entrega': m.entregado_por, 'recibe': m.recibido_por, 'obs': m.observaciones} for m in movs]
    return JsonResponse({'historial': data})

@login_required
@user_passes_test(es_personal_autorizado)
def expedientes_recientes(request):
    recientes = Expediente.objects.all().order_by('-id')[:10]
    data = [{'id': e.id, 'codigo': e.codigo, 'fecha_ingreso': e.fecha_ingreso.strftime("%d/%m/%Y"), 'observaciones': (e.observaciones[:75] + '...') if e.observaciones and len(e.observaciones) > 75 else (e.observaciones or '')} for e in recientes]
    return JsonResponse({'recientes': data})