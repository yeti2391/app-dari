from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
# CAMBIO: Importamos los nombres correctos de las funciones de Excel
from .services import procesar_excel_eventos, procesar_excel_ampliaciones_masivo
from .utils import obtener_estadisticas_periodo, obtener_rango_disponible

def es_dari(user):
    return user.groups.filter(name='DARI').exists() or user.is_superuser

@login_required
@user_passes_test(es_dari)
def dashboard_home(request):
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
    if request.method == 'POST':
        # Procesamiento de Eventos Excel
        if 'csv_eventos' in request.FILES: # Mantenemos el nombre del input por comodidad
            try:
                # CAMBIO: Llamamos a la función de Excel
                nuevos, actualizados = procesar_excel_eventos(request.FILES['csv_eventos'])
                messages.success(request, f"Excel de Eventos procesado. Nuevos: {nuevos}, Actualizados: {actualizados}")
            except Exception as e:
                messages.error(request, f"Error en Excel de Eventos: {e}")

        # Procesamiento de Ampliaciones Excel
        elif 'csv_ampliaciones' in request.FILES:
            try:
                # CAMBIO: Llamamos a la función de Excel
                total = procesar_excel_ampliaciones_masivo(request.FILES.getlist('csv_ampliaciones'))
                messages.success(request, f"Lote finalizado. Se cargaron {total} registros desde archivos Excel.")
            except ValueError as ve:
                messages.error(request, str(ve))
            except Exception as e:
                messages.error(request, f"Error en lote Excel: {e}")
                
        return redirect('dashboard:importar')
    return render(request, 'dashboard/importar.html')

@login_required
@user_passes_test(es_dari)
def generar_informe_anual(request):
    fch_inicio = request.GET.get('inicio')
    fch_fin = request.GET.get('fin')
    
    if not fch_inicio or not fch_fin:
        messages.warning(request, "Seleccione fechas válidas.")
        return redirect('dashboard:home')

    try:
        context = obtener_estadisticas_periodo(fch_inicio, fch_fin)
        context['fch_inicio'] = fch_inicio
        context['fch_fin'] = fch_fin
        return render(request, 'dashboard/informe_anual.html', context)
    except Exception as e:
        print(f"--- ERROR EN INFORME: {e} ---")
        messages.error(request, f"Error al generar el informe: {e}")
        return redirect('dashboard:home')