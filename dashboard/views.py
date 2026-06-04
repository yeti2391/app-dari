from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .services import procesar_csv_eventos, procesar_csv_ampliaciones_masivo
from .utils import obtener_estadisticas_periodo, obtener_rango_disponible

def es_dari(user):
    """Permiso: Solo usuarios del grupo DARI o Superusuarios."""
    return user.groups.filter(name='DARI').exists() or user.is_superuser

@login_required
@user_passes_test(es_dari)
def dashboard_home(request):
    """
    Vista de inicio del Dashboard. 
    Calcula el rango de datos disponibles para configurar los calendarios.
    """
    fch_min, fch_max = obtener_rango_disponible()
    
    context = {
        'disponibilidad': {
            'min': fch_min.strftime('%Y-%m-%d') if fch_min else None,
            'max': fch_max.strftime('%Y-%m-%d') if fch_max else None,
        }
    }
    return render(request, 'dashboard/dashboard.html', context)

@login_required
@user_passes_test(es_dari)
def importar_datos(request):
    """Maneja la lógica de carga de archivos CSV de Eventos y Ampliaciones."""
    if request.method == 'POST':
        # Procesamiento de Eventos (Archivo único)
        if 'csv_eventos' in request.FILES:
            archivo = request.FILES['csv_eventos']
            try:
                nuevos, actualizados = procesar_csv_eventos(archivo)
                messages.success(request, f"Eventos procesados. Nuevos: {nuevos}, Actualizados: {actualizados}")
            except Exception as e:
                messages.error(request, f"Error en Eventos: {e}")

        # Procesamiento de Ampliaciones (Múltiples archivos con validación de nombre)
        elif 'csv_ampliaciones' in request.FILES:
            lista_archivos = request.FILES.getlist('csv_ampliaciones')
            try:
                total = procesar_csv_ampliaciones_masivo(lista_archivos)
                messages.success(request, f"Lote finalizado. Se cargaron {total} registros de {len(lista_archivos)} meses.")
            except ValueError as ve:
                messages.error(request, str(ve))
            except Exception as e:
                messages.error(request, f"Error en lote: {e}")

        return redirect('dashboard:importar')

    return render(request, 'dashboard/importar.html')

@login_required
@user_passes_test(es_dari)
def generar_informe_anual(request):
    """
    Recibe el período desde el formulario y genera el informe web con 
    gráficos y tablas estadísticas.
    """
    fch_inicio = request.GET.get('inicio')
    fch_fin = request.GET.get('fin')
    
    if not fch_inicio or not fch_fin:
        messages.warning(request, "Por favor seleccione un rango de fechas válido.")
        return redirect('dashboard:home')

    try:
        # Obtenemos todo el paquete estadístico desde utils
        context = obtener_estadisticas_periodo(fch_inicio, fch_fin)
        context['fch_inicio'] = fch_inicio
        context['fch_fin'] = fch_fin
        
        return render(request, 'dashboard/informe_anual.html', context)
    except Exception as e:
        messages.error(request, f"Error al generar el informe: {e}")
        return redirect('dashboard:home')