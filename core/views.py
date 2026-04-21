from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, F, Value
from django.db.models.functions import Concat
import json
from .models import *
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied

# Función que verifica si es del grupo DARI
def es_dari(user):
    if user.groups.filter(name='DARI').exists() or user.is_superuser:
        return True
    raise PermissionDenied


# 1. Vista principal
@login_required
@user_passes_test(es_dari)
def home(request):
    return render(request, 'core/home.html')

# 2. Buscar expedientes/personas
@login_required
@user_passes_test(es_dari)
def buscar_expedientes(request):
    query_general = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', 'persona').strip()
    mode = request.GET.get('mode', 'quick').strip()
    
    n1 = request.GET.get('n1', '').strip()
    n2 = request.GET.get('n2', '').strip()
    a1 = request.GET.get('a1', '').strip()
    a2 = request.GET.get('a2', '').strip()
    doc = request.GET.get('doc', '').strip()
    alias = request.GET.get('alias', '').strip()

    if not any([query_general, n1, n2, a1, a2, doc, alias]):
        return JsonResponse({'resultados': []})

    data = []

    # =========================================================
    # CASO A: BÚSQUEDA POR PERSONA (Solo devuelve al que coincide)
    # =========================================================
    if tipo == 'persona':
        # Buscamos directamente en la tabla de vínculos (ExpedientePersona)
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
            # Búsqueda rápida sobre nombre concatenado, documento o alias
            vinculos = vinculos.annotate(
                full_name=Concat(
                    'persona__primer_nombre', Value(' '), 'persona__segundo_nombre', Value(' '),
                    'persona__primer_apellido', Value(' '), 'persona__segundo_apellido',
                    output_field=models.CharField()
                )
            ).filter(
                Q(full_name__icontains=query_general) |
                Q(persona__identificaciones__numero__icontains=query_general) |
                Q(persona__aliases__alias__icontains=query_general)
            )

        # Solo agregamos a los que coincidieron directamente
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
                'nacionalidad_cod': v.persona.nacionalidad.codigo_alpha2 if v.persona.nacionalidad else '---',
                'rol': v.get_rol_display()
            })

    # =========================================================
    # CASO B: BÚSQUEDA POR EXPEDIENTE (Mantiene el comportamiento grupal)
    # =========================================================
    else: 
        query_norm = query_general.upper()
        expedientes = Expediente.objects.filter(
            Q(codigo__icontains=query_norm) |
            Q(observaciones__icontains=query_general) |
            Q(oficina__nombre__icontains=query_general)
        ).select_related('oficina').distinct()

        for exp in expedientes:
            vias = ExpedientePersona.objects.filter(expediente=exp).select_related(
                'persona', 'persona__nacionalidad'
            ).prefetch_related('persona__identificaciones__tipo_documento', 'persona__aliases')
            
            if vias.exists():
                for v in vias:
                    docs = v.persona.identificaciones.all()
                    data.append({
                        'expediente_id': exp.id,
                        'expediente_codigo': exp.codigo,
                        'oficina': exp.oficina.nombre,
                        'fecha_ingreso': exp.fecha_ingreso.strftime("%d/%m/%Y"),
                        'persona_id': v.persona.id,
                        'persona_nombre': f"{v.persona.primer_nombre or ''} {v.persona.primer_apellido or ''}".strip(),
                        'persona_aliases': ", ".join([a.alias for a in v.persona.aliases.all()]),
                        'documento': ", ".join([f"{d.tipo_documento.nombre}: {d.numero}" for d in docs]) if docs else "---",
                        'nacionalidad_cod': v.persona.nacionalidad.codigo_alpha2 if v.persona.nacionalidad else '---',
                        'rol': v.get_rol_display()
                    })
            else:
                # Si el expediente está vacío
                data.append({
                    'expediente_id': exp.id,
                    'expediente_codigo': exp.codigo,
                    'oficina': exp.oficina.nombre,
                    'fecha_ingreso': exp.fecha_ingreso.strftime("%d/%m/%Y"),
                    'persona_id': '',
                    'persona_nombre': '--- SIN ASIGNAR ---',
                    'persona_aliases': '',
                    'documento': '---',
                    'nacionalidad_cod': '---',
                    'rol': 'N/A'
                })
            
    return JsonResponse({'resultados': data})

# 3. Detalles del expediente
@login_required
@user_passes_test(es_dari)
def detalle_expediente(request, id):
    exp = get_object_or_404(Expediente, id=id)
    
    # Traemos personas vinculadas incluyendo sus identificaciones y alias (optimizado con prefetch)
    personas_vinculadas = ExpedientePersona.objects.filter(expediente=exp).select_related(
        'persona', 'persona__nacionalidad'
    ).prefetch_related(
        'persona__identificaciones__tipo_documento', 
        'persona__aliases'
    )
    
    lista_personas = []
    for vp in personas_vinculadas:
        nombre_completo = f"{vp.persona.primer_nombre or ''} {vp.persona.segundo_nombre or ''} {vp.persona.primer_apellido or ''} {vp.persona.segundo_apellido or ''}".strip()

        # 1. Calculamos el string de documentos
        docs_list = vp.persona.identificaciones.all()
        doc_string = ", ".join([f"{d.tipo_documento.nombre}: {d.numero}" for d in docs_list]) if docs_list else "---"
        
        # 2. Calculamos el string de alias
        alias_list = vp.persona.aliases.all()
        alias_string = ", ".join([a.alias for a in alias_list]) if alias_list else ""

        lista_personas.append({
            'persona_id': vp.persona.id,
            'nombre_completo': nombre_completo,
            'primer_nombre': vp.persona.primer_nombre or '',
            'segundo_nombre': vp.persona.segundo_nombre or '',
            'primer_apellido': vp.persona.primer_apellido or '',
            'segundo_apellido': vp.persona.segundo_apellido or '',
            'documento': doc_string,
            'nacionalidad_nombre': vp.persona.nacionalidad.nombre if vp.persona.nacionalidad else 'N/A',
            'rol': vp.get_rol_display(),
            'persona_aliases': alias_string
        })

    # Movimientos para el Timeline de detalles
    movs = ExpedienteMovimiento.objects.filter(expediente=exp).select_related('origen', 'destino').order_by('-fecha')
    lista_movs = []
    for m in movs:
        lista_movs.append({
            'fecha': m.fecha.strftime("%d/%m/%Y %H:%M"),
            'ruta_corta': f"{m.origen.codigo} → {m.destino.codigo}", 
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

@login_required
@user_passes_test(es_dari)
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

@login_required
@user_passes_test(es_dari)
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

# 4. Detalles de Personas
# Obtener todos los datos de una persona
@login_required
@user_passes_test(es_dari)
def detalle_persona(request, id):
    persona = get_object_or_404(Persona, id=id)
    
    # 1. Identificaciones
    identificaciones = []
    for i in persona.identificaciones.all().select_related('tipo_documento'):
        identificaciones.append({
            'id': i.id,
            'tipo': i.tipo_documento.nombre,
            'numero': i.numero
        })
    
    # 2. Alias
    aliases = [a.alias for a in persona.aliases.all()]
    
    # 3. Expedientes donde aparece
    expedientes = []
    vinculos = ExpedientePersona.objects.filter(persona=persona).select_related('expediente', 'expediente__oficina')
    for v in vinculos:
        expedientes.append({
            'id': v.expediente.id,
            'codigo': v.expediente.codigo,
            'oficina': v.expediente.oficina.nombre,
            'rol': v.get_rol_display()
        })

    return JsonResponse({
        'id': persona.id,
        'primer_nombre': persona.primer_nombre,
        'segundo_nombre': persona.segundo_nombre,
        'primer_apellido': persona.primer_apellido,
        'segundo_apellido': persona.segundo_apellido,
        'nacionalidad': persona.nacionalidad.nombre if persona.nacionalidad else 'N/A',
        'identificaciones': identificaciones,
        'aliases': aliases,
        'expedientes': expedientes
    })

# Agregar una nueva identificación a una persona existente
@login_required
@user_passes_test(es_dari)
@csrf_exempt
def agregar_identificacion_persona(request, id):
    if request.method == 'POST':
        data = json.loads(request.body)
        persona = get_object_or_404(Persona, id=id)
        tipo_doc = get_object_or_404(TipoDocumento, id=data['tipo_documento_id'])
        
        # Evitar duplicados
        if Identificacion.objects.filter(tipo_documento=tipo_doc, numero=data['numero'].upper().strip()).exists():
            return JsonResponse({'status': 'error', 'message': 'Ese documento ya está registrado.'}, status=400)
            
        Identificacion.objects.create(
            persona=persona,
            tipo_documento=tipo_doc,
            numero=data['numero']
        )
        return JsonResponse({'status': 'ok'})



# --- OTRAS VISTAS ---

@login_required
@user_passes_test(es_dari)
@csrf_exempt
def actualizar_alfresco(request, id):
    if request.method == 'POST':
        exp = get_object_or_404(Expediente, id=id)
        data = json.loads(request.body)
        exp.subido_alfresco = data.get('estado', False)
        exp.save()
        return JsonResponse({'status': 'ok'})

@login_required
@user_passes_test(es_dari)
@csrf_exempt
def crear_expediente(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        
        # 1. Normalizar la entrada para la validación
        codigo_nuevo = data['codigo'].upper().strip()
        
        # 2. Verificar si ya existe (usamos __iexact para ignorar mayúsculas/minúsculas)
        if Expediente.objects.filter(codigo__iexact=codigo_nuevo).exists():
            return JsonResponse({
                'status': 'error', 
                'message': f'El código de expediente "{codigo_nuevo}" ya existe en el sistema.'
            }, status=400) # Devolvemos un error 400 (Bad Request)
        
        try:
            oficina = Oficina.objects.get(id=data['oficina_id'])
            nuevo_exp = Expediente.objects.create(
                codigo=codigo_nuevo,
                fecha_ingreso=data['fecha'],
                oficina=oficina,
                observaciones=data.get('observaciones', ''),
            )
            return JsonResponse({'status': 'ok', 'id': nuevo_exp.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
@user_passes_test(es_dari)
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

@login_required
@user_passes_test(es_dari)
@csrf_exempt
def vincular_persona(request, id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            expediente = get_object_or_404(Expediente, id=id)
            
            documento_num = data.get('documento', '').strip().upper()
            tipo_doc_id = data.get('tipo_documento_id')
            
            persona = None

            # 1. Intentar encontrar a la persona por su identificación (si se proporcionó)
            if documento_num and tipo_doc_id:
                ident = Identificacion.objects.filter(
                    numero=documento_num, 
                    tipo_documento_id=tipo_doc_id
                ).first()
                if ident:
                    persona = ident.persona

            # 2. Si la persona no existe, la creamos
            if not persona:
                pais = None
                if data.get('nacionalidad_nombre'):
                    pais = Pais.objects.filter(nombre=data['nacionalidad_nombre']).first()
                
                persona = Persona.objects.create(
                    primer_nombre=data.get('primer_nombre'),
                    segundo_nombre=data.get('segundo_nombre', ''),
                    primer_apellido=data.get('primer_apellido'),
                    segundo_apellido=data.get('segundo_apellido', ''),
                    fecha_nacimiento=data.get('fecha_nacimiento') or None,
                    nacionalidad=pais
                )
                
                # Creamos su primera identificación si hay datos
                if documento_num and tipo_doc_id:
                    Identificacion.objects.create(
                        persona=persona,
                        tipo_documento_id=tipo_doc_id,
                        numero=documento_num
                    )
            else:
                # Si la persona ya existía, opcionalmente actualizamos sus nombres
                persona.primer_nombre = data.get('primer_nombre', persona.primer_nombre)
                persona.primer_apellido = data.get('primer_apellido', persona.primer_apellido)
                persona.save()

            # 3. Crear el vínculo con el Expediente
            ExpedientePersona.objects.get_or_create(
                expediente=expediente,
                persona=persona,
                defaults={'rol': data.get('rol', 'indagado').lower()}
            )

            # 4. Gestión de Alias (pueden ser varios separados por coma)
            if data.get('alias'):
                lista_alias = data['alias'].split(',')
                for a in lista_alias:
                    nombre_alias = a.strip().upper()
                    if nombre_alias:
                        Alias.objects.get_or_create(persona=persona, alias=nombre_alias)

            return JsonResponse({
                'status': 'ok',
                'persona_id': persona.id
                })
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
@user_passes_test(es_dari)
@csrf_exempt
def desvincular_persona(request, id): # 'id' es el ID del expediente
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            persona_id = data.get('persona_id')
            
            # Buscamos la relación en la tabla intermedia y la borramos
            vinculo = ExpedientePersona.objects.filter(expediente_id=id, persona_id=persona_id)
            
            if vinculo.exists():
                vinculo.delete()
                return JsonResponse({'status': 'ok'})
            else:
                return JsonResponse({'status': 'error', 'message': 'La vinculación no existe'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
@user_passes_test(es_dari)       
@csrf_exempt
def agregar_alias_persona(request, id):
    if request.method == 'POST':
        data = json.loads(request.body)
        persona = get_object_or_404(Persona, id=id)
        alias_texto = data.get('alias', '').strip().upper()
        
        if alias_texto:
            # Evitamos duplicados para la misma persona
            Alias.objects.get_or_create(persona=persona, alias=alias_texto)
            return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)

# Vincular una persona que YA EXISTE al expediente
@login_required
@user_passes_test(es_dari)
@csrf_exempt
def vincular_persona_existente(request, id):
    if request.method == 'POST':
        data = json.loads(request.body)
        expediente = get_object_or_404(Expediente, id=id)
        persona = get_object_or_404(Persona, id=data['persona_id'])
        
        # Creamos el vínculo (evitando duplicados en el mismo expediente)
        ExpedientePersona.objects.get_or_create(
            expediente=expediente,
            persona=persona,
            defaults={'rol': data.get('rol', 'indagado').lower()}
        )
        return JsonResponse({'status': 'ok'})