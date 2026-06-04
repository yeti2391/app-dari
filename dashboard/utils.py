from django.db import connection
from django.db.models import Min, Max
from .models import NovedadEstadistica, AmpliacionEstadistica

def ejecutar_query_dict(query, params=None):
    """
    Ejecuta SQL raw y mapea los resultados a una lista de diccionarios.
    Útil para manejar consultas complejas que el ORM de Django no cubre fácilmente.
    """
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        # Obtenemos los nombres de las columnas para las llaves del diccionario
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

def obtener_rango_disponible():
    """
    Calcula los límites de fecha (mínimo y máximo) de los datos cargados.
    Utiliza el ORM para mayor velocidad y limpieza.
    """
    # Buscamos el rango en las novedades registradas
    rango = NovedadEstadistica.objects.aggregate(
        inicio=Min('fecha_ingreso'),
        fin=Max('fecha_ingreso')
    )
    
    # Si no hay datos, retornamos Nones para que el view maneje el estado vacío
    if not rango['inicio']:
        return None, None
        
    return rango['inicio'], rango['fin']

def obtener_estadisticas_periodo(fch_inicio, fch_fin):
    """
    Motor de cálculo estadístico. Procesa las 6 áreas clave del informe 
    utilizando las nuevas tablas procesadas por la app Dashboard.
    """
    
    # 1. Total de Novedades Propias en el período
    q1 = """
        SELECT COUNT(DISTINCT nro) AS total 
        FROM dashboard_novedadestadistica 
        WHERE fecha_ingreso >= %s AND fecha_ingreso <= %s
    """
    res_total = ejecutar_query_dict(q1, [fch_inicio, fch_fin])
    total_novedades = res_total[0]['total'] if res_total else 0

    # 2. Distribución de Novedades Propias por Dependencia (Gráfico de Barras)
    q2 = """
        SELECT dependencia_alias, COUNT(DISTINCT nro) AS cantidad
        FROM dashboard_novedadestadistica
        WHERE fecha_ingreso >= %s AND fecha_ingreso <= %s
        GROUP BY dependencia_alias 
        ORDER BY cantidad DESC
    """
    deps_novedades = ejecutar_query_dict(q2, [fch_inicio, fch_fin])

    # 3. Estado de N.U.N.C. (Novedades con/sin Fiscalía - Gráfico de Torta)
    q3 = """
        SELECT 
            CASE WHEN (nunc IS NULL OR nunc = '') THEN 'Sin N.U.N.C.' ELSE 'Con N.U.N.C.' END AS categoria,
            COUNT(DISTINCT nro) AS cantidad
        FROM dashboard_novedadestadistica
        WHERE fecha_ingreso >= %s AND fecha_ingreso <= %s
        GROUP BY categoria
    """
    nunc_stats = ejecutar_query_dict(q3, [fch_inicio, fch_fin])

    # 4. Novedades Externas (Casos de otras unidades donde la DGLCCO intervino)
    # Se detectan mediante un LEFT JOIN: están en ampliaciones pero no en novedades propias
    q4 = """
        SELECT a.dependencia_alias, COUNT(DISTINCT a.denuncia_madre) AS cantidad
        FROM dashboard_ampliacionestadistica a
        LEFT JOIN dashboard_novedadestadistica n ON a.denuncia_madre = n.nro
        WHERE n.nro IS NULL 
          AND a.periodo >= LEFT(%s, 7) AND a.periodo <= LEFT(%s, 7)
        GROUP BY a.dependencia_alias 
        ORDER BY cantidad DESC
    """
    novedades_externas = ejecutar_query_dict(q4, [fch_inicio, fch_fin])

    # 5. Evolución Mensual de Actividad (Línea de tiempo)
    q5 = """
        SELECT TO_CHAR(fecha_ingreso, 'YYYY-MM') AS periodo, COUNT(DISTINCT nro) AS cantidad
        FROM dashboard_novedadestadistica
        WHERE fecha_ingreso >= %s AND fecha_ingreso <= %s
        GROUP BY periodo 
        ORDER BY periodo
    """
    evolucion_mensual = ejecutar_query_dict(q5, [fch_inicio, fch_fin])

    # 6. Consolidado de Allanamientos (Suma de positivos y negativos de ambas fuentes)
    q6 = """
        WITH total_allanamientos AS (
            -- Allanamientos de Novedades Propias
            SELECT nro, MAX(allanamientos_pos) as p, MAX(allanamientos_neg) as n
            FROM dashboard_novedadestadistica 
            WHERE fecha_ingreso >= %s AND fecha_ingreso <= %s
            GROUP BY nro
            
            UNION ALL
            
            -- Allanamientos de Ampliaciones (incluyendo novedades externas)
            SELECT denuncia_madre, MAX(allanamientos_pos), MAX(allanamientos_neg)
            FROM dashboard_ampliacionestadistica 
            WHERE periodo >= LEFT(%s, 7) AND periodo <= LEFT(%s, 7)
            GROUP BY denuncia_madre
        ),
        agrupado AS (
            -- Consolidamos por número de novedad para no duplicar si hay datos en ambas tablas
            SELECT nro, MAX(p) as p, MAX(n) as n 
            FROM total_allanamientos 
            GROUP BY nro
        )
        SELECT 
            COALESCE(SUM(p), 0) AS positivos, 
            COALESCE(SUM(n), 0) AS negativos, 
            COALESCE(SUM(p + n), 0) AS total 
        FROM agrupado
    """
    res_allan = ejecutar_query_dict(q6, [fch_inicio, fch_fin, fch_inicio, fch_fin])
    allanamientos = res_allan[0] if res_allan else {'positivos': 0, 'negativos': 0, 'total': 0}

    # Retorno unificado de resultados
    return {
        'total_novedades': total_novedades,
        'deps_novedades': deps_novedades,
        'nunc_stats': nunc_stats,
        'novedades_externas': novedades_externas,
        'evolucion_mensual': evolucion_mensual,
        'allanamientos': allanamientos,
    }