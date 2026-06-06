from django.db import connection
from django.db.models import Min, Max
from .models import NovedadEstadistica, AmpliacionEstadistica

def ejecutar_query_dict(query, params=None):
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

def obtener_rango_disponible():
    rango = NovedadEstadistica.objects.aggregate(
        inicio=Min('fecha_ingreso'),
        fin=Max('fecha_ingreso')
    )
    if not rango['inicio']:
        return None, None
    return rango['inicio'], rango['fin']

def obtener_estadisticas_periodo(fch_inicio, fch_fin):
    # Preparamos periodos para las tablas de ampliaciones (YYYY-MM)
    per_inicio = fch_inicio[:7]
    per_fin = fch_fin[:7]
    
    # 1. Total Novedades
    q1 = "SELECT COUNT(DISTINCT nro) AS total FROM dashboard_novedadestadistica WHERE fecha_ingreso >= %s AND fecha_ingreso <= %s"
    res_total = ejecutar_query_dict(q1, [fch_inicio, fch_fin])
    total_novedades = res_total[0]['total'] if res_total else 0

    # 2. Distribución por Dependencia (Con Porcentaje)
    q2 = """
        SELECT dependencia_alias, COUNT(DISTINCT nro) AS cantidad,
        ROUND(COUNT(DISTINCT nro) * 100.0 / SUM(COUNT(DISTINCT nro)) OVER (), 2) as porcentaje
        FROM dashboard_novedadestadistica WHERE fecha_ingreso >= %s AND fecha_ingreso <= %s
        GROUP BY dependencia_alias ORDER BY cantidad DESC
    """
    deps_novedades = ejecutar_query_dict(q2, [fch_inicio, fch_fin])

    # 3. Estado de N.U.N.C. (Variable que faltaba definir correctamente)
    q3 = """
        SELECT CASE WHEN (nunc IS NULL OR nunc = '') THEN 'Sin N.U.N.C.' ELSE 'Con N.U.N.C.' END AS categoria,
        COUNT(DISTINCT nro) AS cantidad
        FROM dashboard_novedadestadistica WHERE fecha_ingreso >= %s AND fecha_ingreso <= %s
        GROUP BY categoria
    """
    nunc_stats = ejecutar_query_dict(q3, [fch_inicio, fch_fin]) # <--- DEFINICIÓN CLAVE

    # 4. Ampliaciones (Con Porcentaje)
    q4 = """
        SELECT dependencia_alias, COUNT(*) AS cantidad,
        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as porcentaje
        FROM dashboard_ampliacionestadistica WHERE periodo >= %s AND periodo <= %s
        GROUP BY dependencia_alias ORDER BY cantidad DESC
    """
    deps_ampliaciones = ejecutar_query_dict(q4, [per_inicio, per_fin])

    # 5. Novedades Externas
    q5 = """
        SELECT a.dependencia_alias, COUNT(DISTINCT a.denuncia_madre) AS cantidad
        FROM dashboard_ampliacionestadistica a
        LEFT JOIN dashboard_novedadestadistica n ON a.denuncia_madre = n.nro
        WHERE n.nro IS NULL AND a.periodo >= %s AND a.periodo <= %s
        GROUP BY a.dependencia_alias ORDER BY cantidad DESC
    """
    novedades_externas = ejecutar_query_dict(q5, [per_inicio, per_fin])

    # 6. Evolución Mensual
    q6 = """
        SELECT TO_CHAR(fecha_ingreso, 'YYYY-MM') AS periodo, COUNT(DISTINCT nro) AS cantidad
        FROM dashboard_novedadestadistica WHERE fecha_ingreso >= %s AND fecha_ingreso <= %s
        GROUP BY periodo ORDER BY periodo
    """
    evolucion_mensual = ejecutar_query_dict(q6, [fch_inicio, fch_fin])

    # 7. Allanamientos
    q7 = """
        WITH total_allan AS (
            SELECT nro, MAX(allanamientos_pos) as p, MAX(allanamientos_neg) as n FROM dashboard_novedadestadistica WHERE fecha_ingreso >= %s AND fecha_ingreso <= %s GROUP BY nro
            UNION ALL
            SELECT denuncia_madre, MAX(allanamientos_pos), MAX(allanamientos_neg) FROM dashboard_ampliacionestadistica WHERE periodo >= %s AND periodo <= %s GROUP BY denuncia_madre
        )
        SELECT COALESCE(SUM(p), 0) AS positivos, COALESCE(SUM(n), 0) AS negativos, COALESCE(SUM(p+n), 0) AS total 
        FROM (SELECT nro, MAX(p) as p, MAX(n) as n FROM total_allan GROUP BY nro) as t
    """
    res_allan = ejecutar_query_dict(q7, [fch_inicio, fch_fin, per_inicio, per_fin])
    allanamientos = res_allan[0] if res_allan else {'positivos': 0, 'negativos': 0, 'total': 0}

    return {
        'total_novedades': total_novedades,
        'deps_novedades': deps_novedades,
        'nunc_stats': nunc_stats,
        'deps_ampliaciones': deps_ampliaciones,
        'novedades_externas': novedades_externas,
        'evolucion_mensual': evolucion_mensual,
        'allanamientos': allanamientos,
    }