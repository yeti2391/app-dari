# core/middleware.py
from django.http import HttpResponseForbidden

ALLOWED_IPS = ['10.42.1.55', '10.42.1.59', '10.42.1.62', '127.0.0.1']  # las IPs que quieres permitir en caso de querer un rango en lugar de IP especificas usar '10.42.1.0/24'

class RestrictIPMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = request.META.get('REMOTE_ADDR')
        if ip not in ALLOWED_IPS:
            return HttpResponseForbidden("Acceso denegado")
        return self.get_response(request)
