from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .services import procesar_csv_eventos, procesar_csv_ampliaciones_masivo
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
    """
    Controlador central para la subida de datos estadísticos del SGSP.
    
    Procesa dos tipos de fuentes:
    1. Eventos (Novedades): Un solo archivo que actualiza o inserta registros.
    2. Ampliaciones: Múltiples archivos que deben cumplir el formato YYYY-MM.csv
       para asignar automáticamente el periodo estadístico.
    """
    
    if request.method == 'POST':
        
        # --- CASO A: PROCESAMIENTO DE EVENTOS (NOVEDADES) ---
        if 'csv_eventos' in request.FILES:
            archivo = request.FILES['csv_eventos']
            try:
                # La función retorna la cantidad de registros nuevos y actualizados
                nuevos, actualizados = procesar_csv_eventos(archivo)
                messages.success(request, 
                    f"Eventos procesados con éxito. Registros nuevos: {nuevos}, Actualizados: {actualizados}")
            except Exception as e:
                # Captura errores de formato CSV, encoding o de base de datos
                messages.error(request, f"Error crítico al procesar Eventos: {e}")

        # --- CASO B: PROCESAMIENTO MASIVO DE AMPLIACIONES E INFORMES ---
        elif 'csv_ampliaciones' in request.FILES:
            # Obtenemos la lista completa de archivos (atributo 'multiple' del HTML)
            lista_archivos = request.FILES.getlist('csv_ampliaciones')
            try:
                # Procesamos el lote. El service valida que los nombres sean YYYY-MM.csv
                total_registros = procesar_csv_ampliaciones_masivo(lista_archivos)
                messages.success(request, 
                    f"Lote de Ampliaciones finalizado. Se cargaron {total_registros} registros de {len(lista_archivos)} archivos mensuales.")
            
            except ValueError as ve:
                # Captura específicamente errores de validación de nombres de archivo
                messages.error(request, f"Validación de archivos fallida: {ve}")
            
            except Exception as e:
                # Captura otros errores inesperados
                messages.error(request, f"Error inesperado en carga masiva de Ampliaciones: {e}")

        # Después de procesar cualquiera de los dos, redirigimos a la misma página
        # para limpiar el formulario y mostrar los mensajes de éxito/error.
        return redirect('dashboard:importar')

    # Renderizado inicial de la página (Petición GET)
    return render(request, 'dashboard/importar.html')

# 3. Vista del Informe Estadístico
@login_required
@user_passes_test(es_dari)
def generar_informe_anual(request):
    # Capturamos las fechas del formulario. Si no hay, ponemos un default.
    fch_inicio = request.GET.get('inicio', '2025-03-01')
    fch_fin = request.GET.get('fin', '2026-02-28')
    
    try:
        # Llamamos al motor estadístico con las fechas elegidas
        context = obtener_estadisticas_periodo(fch_inicio, fch_fin)
        context['fch_inicio'] = fch_inicio
        context['fch_fin'] = fch_fin
        
        return render(request, 'dashboard/informe_anual.html', context)
    except Exception as e:
        messages.error(request, f"Error al procesar el período seleccionado: {e}")
        return redirect('dashboard:home')