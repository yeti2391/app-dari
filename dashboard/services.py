import csv
import io
from datetime import datetime
from .models import EventoSGSP

def limpiar_fecha(txt):
    if not txt or txt.strip() == "": return None
    try:
        # El SGSP exporta como DD/MM/YYYY HH:MM
        return datetime.strptime(txt.strip(), '%d/%m/%Y %H:%M')
    except ValueError:
        return None

def limpiar_float(txt):
    if not txt: return 0.0
    # Cambiamos la coma por punto para que Postgres lo acepte como float
    return float(str(txt).replace(',', '.'))

def procesar_csv_eventos(archivo):
    # Leer el archivo decodificando a UTF-8
    decoded_file = archivo.read().decode('utf-8')
    io_string = io.StringIO(decoded_file)
    # El delimitador es ; según indicaste
    reader = csv.DictReader(io_string, delimiter=';')
    
    conteo_nuevos = 0
    conteo_actualizados = 0

    for row in reader:
        # Usamos update_or_create basado en la PK 'nro'
        obj, created = EventoSGSP.objects.using('default').update_or_create(
            nro=row['Nro'],
            defaults={
                'noticiaunicacriminal': int(row['NoticiaUnicaCriminal']) if row['NoticiaUnicaCriminal'] else None,
                'hecho': limpiar_fecha(row['Hecho']),
                'conocimiento': limpiar_fecha(row['Conocimiento']),
                'ingreso': limpiar_fecha(row['Ingreso']),
                'u_ejecutora_origen': row['U Ejecutora Origen'],
                'dependencia_origen': row['Dependencia Origen'],
                'dependencia_actual': row['Dependencia Actual'],
                'titulo': row['Título'],
                'aclarada': row['Aclarada'],
                'x': limpiar_float(row['X']),
                'y': limpiar_float(row['Y']),
                'total_allanamientos_positivos': int(row['Total Allanamientos Positivos']) if row['Total Allanamientos Positivos'] else 0,
                'total_allanamientos_negativos': int(row['Total Allanamientos Negativos']) if row['Total Allanamientos Negativos'] else 0,
                # Agrega aquí el resto de campos que necesites...
            }
        )
        if created: conteo_nuevos += 1
        else: conteo_actualizados += 1

    return conteo_nuevos, conteo_actualizados