"""
Django settings for DARI project.

SETTINGS CONFIGURADO PARA PRODUCCIÓN 

Base de datos en POSTGRESQL

"""
# proyecto/settings/local.py
from .base import *

# Leemos el modo Debug desde el .env
DEBUG = os.getenv('DEBUG') == 'True'

ALLOWED_HOSTS = ['10.42.1.59', 'localhost', '127.0.0.1', '0.0.0.0'] #cambiar por la IP de la computadora usada de host

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}