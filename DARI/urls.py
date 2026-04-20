"""
URL configuration for DARI project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

# Vista rápida para redirigir según el grupo al loguearse
def login_success(request):
    if request.user.groups.filter(name='DARI').exists():
        return redirect('/DARI/')
    elif request.user.groups.filter(name='DRBPA').exists():
        return redirect('/DRBPA/')
    else:
        return redirect('/admin/') # O una página de "Sin Permiso"
    
urlpatterns = [
     path('admin/', admin.site.urls),    
    # Rutas de autenticación (login, logout)
    path('accounts/', include('django.contrib.auth.urls')),    
    # Redirección inteligente tras el login
    path('login-success/', login_success, name='login_success'),
    # APPS POR DEPARTAMENTO
    path('DARI/', include('core.urls')),
    # path('DRBPA/', include('drbpa.urls')), # Futura app    
    # Si alguien entra a la raíz, mandarlo al login
    path('', lambda req: redirect('login')),

]
