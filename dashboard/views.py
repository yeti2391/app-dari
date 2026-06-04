from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .services import procesar_csv_eventos
from .utils import obtener_estadisticas_periodo

# Función de verificación de grupo (Misma lógica que en core)
def es_dari(user):
    return user.groups.filter(name='DARI').exists() or user.is_superuser

# 1. Vista principal del Dashboard
@login_required
@user_passes_test(es_dari)
def dashboard_home(request):
    """Renderiza el panel de control de estadísticas"""
    return render(request, 'dashboard/dashboard.html')

# 2. Vista de Importación
@login_required
@user_passes_test(es_dari)
def importar_datos(request):
    """Maneja la subida y procesamiento de archivos CSV"""
    if request.method == 'POST' and request.FILES.get('csv_eventos'):
        archivo = request.FILES['csv_eventos']
        try:
            nuevos, actualizados = procesar_csv_eventos(archivo)
            messages.success(request, f"Proceso finalizado. Registros nuevos: {nuevos}, Actualizados: {actualizados}")
        except Exception as e:
            messages.error(request, f"Error crítico al procesar el archivo: {e}")
        return redirect('dashboard:importar')
        
    return render(request, 'dashboard/importar.html')

# 3. Vista del Informe Estadístico
@login_required
@user_passes_test(es_dari)
def generar_informe_anual(request):
    """Calcula las estadísticas y renderiza el informe web"""
    # Fechas por defecto según tu informe original
    fch_inicio = request.GET.get('inicio', '2025-03-01')
    fch_fin = request.GET.get('fin', '2026-03-01')
    
    try:
        context = obtener_estadisticas_periodo(fch_inicio, fch_fin)
        context['fch_inicio'] = fch_inicio
        context['fch_fin'] = fch_fin
        return render(request, 'dashboard/informe_anual.html', context)
    except Exception as e:
        messages.error(request, f"Error al generar las estadísticas: {e}")
        return redirect('dashboard:home')