import csv, io, re
from datetime import datetime
from .models import NovedadEstadistica, AmpliacionEstadistica

# Diccionario de mapeo para convertir nombres largos en Alias cortos
MAPEO_DEPENDENCIAS = {
    'DGLCCO INTERPOL - AYUDANTÍA Y SECRETARÍA DIRECTOR': 'AYUDANTÍA',
    'DGLCCO INTERPOL – DPTO. INV. DELITOS ESPECIALES': 'DIDE',
    'DGLCCO INTERPOL – DPTO ANÁLISIS Y REG INFORMACIÓN': 'DARI',
    'DGLCCO INTERPOL - OF. GUARDIA Y CENTRAL TELEFÓNICA': 'GUARDIA',
    'DGLCCO INTERPOL – DPTO. POBLACIÓN FLOTANTE': 'DPF',
    'DGLCCO INTERPOL – DPTO. INV. DELITOS FINANCIEROS': 'DIDF',
    'DGLCCO INTERPOL – DPTO INV ANÁLISIS TRÁF AUTOMOTOR': 'DATA',
    'DGLCCO INTERPOL - SECCIÓN LAVADO DE ACTIVOS': 'SLA',
    'DGLCCO INTERPOL – DPTO. COMUNICACIONES I24/7': 'I24/7',
    'DGLCCO INTERPOL – DPTO. CAPTURAS INTERNACIONALES': 'DCI',
    'DGLCCO INTERPOL – DPTO. ASUNTOS INTERNACIONALES': 'DAI',
    'DGLCCO INTERPOL – DPTO REG Y BÚS PERSONAS AUSENTES': 'DRBPA',
}

def obtener_alias(nombre_largo):
    for largo, corto in MAPEO_DEPENDENCIAS.items():
        if largo in nombre_largo: return corto
    return nombre_largo[:15] # Fallback por si no coincide

def limpiar_fecha(txt):
    if not txt or str(txt).lower() == 'null': return None
    try:
        return datetime.strptime(txt.strip(), '%d/%m/%Y %H:%M')
    except:
        try: return datetime.strptime(txt.strip(), '%Y-%m-%d %H:%M:%S')
        except: return None

def procesar_csv_eventos(archivo):
    content = archivo.read().decode('utf-8')
    reader = csv.DictReader(io.StringIO(content), delimiter=';')
    nuevos, actualizados = 0, 0

    for row in reader:
        r = {k.lower(): v for k, v in row.items()}
        obj, created = NovedadEstadistica.objects.update_or_create(
            nro=r['nro'],
            defaults={
                'nunc': r.get('noticiaunicacriminal'),
                'fecha_ingreso': limpiar_fecha(r.get('ingreso')),
                'dependencia_original': r.get('dependencia actual', ''),
                'dependencia_alias': obtener_alias(r.get('dependencia actual', '')),
                'titulo': r.get('título', ''),
                'aclarada': r.get('aclarada', '').lower() == 'si',
                'allanamientos_pos': int(r.get('total allanamientos positivos', 0)),
                'allanamientos_neg': int(r.get('total allanamientos negativos', 0)),
            }
        )
        if created: nuevos += 1
        else: actualizados += 1
    return nuevos, actualizados

def procesar_csv_ampliaciones_masivo(lista_archivos):
    total = 0
    for archivo in lista_archivos:
        # Validar nombre YYYY-MM.csv
        match = re.search(r'(\d{4}-\d{2})', archivo.name)
        if not match: continue
        periodo = match.group(1)
        
        reader = csv.DictReader(io.StringIO(archivo.read().decode('utf-8')), delimiter=';')
        for row in reader:
            r = {k.lower(): v for k, v in row.items()}
            AmpliacionEstadistica.objects.update_or_create(
                nro=r['nro'],
                defaults={
                    'denuncia_madre': r.get('denuncia'),
                    'fecha_denuncia': limpiar_fecha(r.get('ingreso denuncia')),
                    'titulo': r.get('título', ''),
                    'dependencia_alias': obtener_alias(r.get('dependencia ampliacion', '')),
                    'tipo': r.get('tipo', 'AMP'),
                    'periodo': periodo,
                    'allanamientos_pos': int(r.get('total allanamientos positivos', 0)),
                    'allanamientos_neg': int(r.get('total allanamientos negativos', 0)),
                }
            )
            total += 1
    return total