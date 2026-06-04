import csv
import io
import re
from datetime import datetime
from django.utils import timezone
from .models import NovedadEstadistica, AmpliacionEstadistica

def limpiar_fecha_sql(txt):
    if not txt or str(txt).lower() in ['null', '']: return None
    txt = str(txt).strip()
    dt = None
    try:
        # Formato ISO (2025-03-28) o SGSP (28/03/2025)
        if '-' in txt:
            dt = datetime.strptime(txt[:19], '%Y-%m-%d %H:%M:%S')
        elif '/' in txt:
            dt = datetime.strptime(txt, '%d/%m/%Y %H:%M')
        
        if dt:
            return timezone.make_aware(dt, timezone.get_current_timezone())
    except:
        return None
    return None

def limpiar_int(val):
    if val is None or str(val).strip() == "": return 0
    try:
        return int(float(str(val).replace(',', '.')))
    except: return 0

def obtener_alias(nombre_largo):
    """
    Mapeo de nombres oficiales del SGSP a siglas de la Dirección.
    Maneja valores None y diferentes tipos de guiones.
    """
    if not nombre_largo:
        return "OTRA"
        
    # Normalizamos el nombre: mayúsculas, quitamos espacios y estandarizamos guiones
    n = str(nombre_largo).upper().replace('–', '-').strip()

    MAPEO = {
        "DGLCCO INTERPOL - AYUDANTÍA Y SECRETARÍA DIRECTOR": "AYUDANTÍA",
        "DGLCCO INTERPOL - DPTO. INV. DELITOS ESPECIALES": "DIDE",
        "DGLCCO INTERPOL - DPTO ANÁLISIS Y REG INFORMACIÓN": "DARI",
        "DGLCCO INTERPOL - OF. GUARDIA Y CENTRAL TELEFÓNICA": "GUARDIA",
        "DGLCCO INTERPOL - DPTO. POBLACIÓN FLOTANTE": "DPF",
        "DGLCCO INTERPOL - DPTO. INV. DELITOS FINANCIEROS": "DIDF",
        "DGLCCO INTERPOL - DPTO INV ANÁLISIS TRÁF AUTOMOTOR": "DATA",
        "DGLCCO INTERPOL - SECCIÓN LAVADO DE ACTIVOS": "SLA",
        "DGLCCO INTERPOL - DPTO. COMUNICACIONES I24/7": "I24/7",
        "DGLCCO INTERPOL - DPTO. CAPTURAS INTERNACIONALES": "DCI",
        "DGLCCO INTERPOL - DPTO. ASUNTOS INTERNACIONALES": "DAI",
        "DGLCCO INTERPOL - DPTO REG Y BÚS PERSONAS AUSENTES": "DRBPA"
    }

    # Buscamos coincidencia exacta o contenida
    for nombre_oficial, sigla in MAPEO.items():
        if nombre_oficial in n:
            return sigla
            
    return "OTRA"

def procesar_csv_eventos(archivo):
    content = archivo.read().decode('utf-8')
    reader = csv.DictReader(io.StringIO(content), delimiter=';')
    nuevos, actualizados = 0, 0

    for row in reader:
        # Normalizamos encabezados: minúsculas, sin espacios, quitamos caracteres raros
        r = {str(k).lower().strip(): v for k, v in row.items() if k is not None}
        
        nro_nov = r.get('nro')
        if not nro_nov: continue

        # Extraemos dependencia con fallback para evitar el error de 'NoneType'
        dep_larga = r.get('dependencia actual') or r.get('dependencia origen') or ''

        obj, created = NovedadEstadistica.objects.update_or_create(
            nro=nro_nov,
            defaults={
                'nunc': r.get('noticiaunicacriminal'),
                'fecha_ingreso': limpiar_fecha_sql(r.get('ingreso')),
                'dependencia_original': dep_larga,
                'dependencia_alias': obtener_alias(dep_larga),
                'titulo': r.get('título', 'SIN TÍTULO'),
                'aclarada': str(r.get('aclarada', '')).lower() == 'si',
                'allanamientos_pos': limpiar_int(r.get('total allanamientos positivos')),
                'allanamientos_neg': limpiar_int(r.get('total allanamientos negativos')),
            }
        )
        if created: nuevos += 1
        else: actualizados += 1
    return nuevos, actualizados

def procesar_csv_ampliaciones_masivo(lista_archivos):
    total = 0
    for archivo in lista_archivos:
        match = re.search(r'(\d{4}-\d{2})', archivo.name)
        if not match: continue
        periodo = match.group(1)
        
        reader = csv.DictReader(io.StringIO(archivo.read().decode('utf-8')), delimiter=';')
        for row in reader:
            r = {str(k).lower().strip(): v for k, v in row.items() if k is not None}
            if not r.get('nro'): continue

            dep_larga = r.get('dependencia ampliacion') or ''

            AmpliacionEstadistica.objects.update_or_create(
                nro=r['nro'],
                defaults={
                    'denuncia_madre': r.get('denuncia'),
                    'fecha_denuncia': limpiar_fecha_sql(r.get('ingreso denuncia')),
                    'titulo': r.get('título', 'SIN TÍTULO'),
                    'dependencia_alias': obtener_alias(dep_larga),
                    'tipo': r.get('tipo', 'AMP'),
                    'periodo': periodo,
                    'allanamientos_pos': limpiar_int(r.get('total allanamientos positivos')),
                    'allanamientos_neg': limpiar_int(r.get('total allanamientos negativos')),
                }
            )
            total += 1
    return total