"""
Django settings for DARI project.

PARA PRUEBAS BASES DE DATOS EN SQLITE, NO USAR EN PRODUCCIÓN
"""
from .base import *
# core/middleware.py
from django.http import HttpResponseForbidden

ALLOWED_IPS = ['10.42.1.59', 'localhost', '127.0.0.1', '0.0.0.0'] # la IP que quieres permitir

DEBUG = True

SECRET_KEY = 'django-insecure-nwe#4qnjmdt6q14k#)*j!g1_&@-z4r_pdqkmr6biv_=mqq^2cl'

# En pruebas usamos SQLite porque es más rápido y volátil
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'test_db.sqlite3',
    }
}

# Desactivar hashing de passwords complejo para acelerar los tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]


# Agregamos el middleware de restricción
MIDDLEWARE += [
    'core.middleware.RestrictIPMiddleware',
]
