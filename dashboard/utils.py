from django.db import connection
from datetime import datetime

def ejecutar_query_dict(query, params=None):
    """Ejecuta SQL raw y devuelve una lista de diccionarios"""
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

def obtener_estadisticas_periodo(fch_inicio, fch_fin):
    """
    Recibe fechas en formato 'YYYY-MM-DD'
    Retorna un diccionario con todos los resultados de tus 10 querys.
    """
    
    # 1. Total Novedades
    q1 = "SELECT COUNT(DISTINCT nro) AS total FROM exportados.v_dglcco_alias WHERE ingreso >= %s AND ingreso < %s"
    total_novedades = ejecutar_query_dict(q1, [fch_inicio, fch_fin])[0]['total']

    # 2. Distribución por Dependencia (Gráfico de Barras Pág 3)
    q2 = """
        SELECT dependencia_alias, COUNT(DISTINCT nro) AS cantidad
        FROM exportados.v_dglcco_alias
        WHERE ingreso >= %s AND ingreso < %s
        GROUP BY dependencia_alias ORDER BY cantidad DESC
    """
    deps_novedades = ejecutar_query_dict(q2, [fch_inicio, fch_fin])

    # 3. Novedades sin Fiscalía (Gráfico de Torta Pág 10)
    q7 = """
        SELECT 
            CASE WHEN noticiaunicacriminal IS NULL THEN 'Sin N.U.N.C.' ELSE 'Con N.U.N.C.' END AS categoria,
            COUNT(DISTINCT nro) AS cantidad
        FROM exportados.v_dglcco_alias
        WHERE ingreso >= %s AND ingreso < %s
        GROUP BY categoria
    """
    nunc_stats = ejecutar_query_dict(q7, [fch_inicio, fch_fin])

    # 4. Total de Allanamientos (Consolidado Pág 14-15)
    # Usamos tu Query 10 con los parámetros de fecha
    q10 = """
        WITH allanamientos AS (
            SELECT nro, COALESCE(total_allanamientos_positivos, 0) AS pos, COALESCE(total_allanamientos_negativos, 0) AS neg
            FROM exportados.v_dglcco_alias WHERE ingreso >= %s AND ingreso < %s
            UNION ALL
            SELECT denuncia AS nro, COALESCE(total_allanamientos_positivos, 0), COALESCE(total_allanamientos_negativos, 0)
            FROM exportados.v_dglcco_ampeinfo_alias WHERE periodo >= LEFT(%s, 7) AND periodo < LEFT(%s, 7)
        ),
        consolidado AS (
            SELECT nro, MAX(pos) AS pos, MAX(neg) AS neg FROM allanamientos GROUP BY nro
        )
        SELECT SUM(pos) AS positivos, SUM(neg) AS negativos, SUM(pos + neg) AS total FROM consolidado
    """
    allanamientos = ejecutar_query_dict(q10, [fch_inicio, fch_fin, fch_inicio, fch_fin])[0]

    # 5. Evolución Mensual (Gráfico de Líneas Pág 7-9)
    q5 = """
        SELECT TO_CHAR(ingreso, 'YYYY-MM') AS periodo, COUNT(DISTINCT nro) AS cantidad
        FROM exportados.v_dglcco_alias
        WHERE ingreso >= %s AND ingreso < %s
        GROUP BY periodo ORDER BY periodo
    """
    evolucion_mensual = ejecutar_query_dict(q5, [fch_inicio, fch_fin])

    return {
        'total_novedades': total_novedades,
        'deps_novedades': deps_novedades,
        'nunc_stats': nunc_stats,
        'allanamientos': allanamientos,
        'evolucion_mensual': evolucion_mensual,
    }