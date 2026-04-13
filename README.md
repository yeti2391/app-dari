# App de Gestión Documental DARI

## Descripción

Esta aplicación web es un sistema completo para la gestión documental y administrativa del **DARI (Dirección de Asuntos Registrales e Identificación)**. Desarrollada con Django y Vue.js, permite la administración eficiente de expedientes, personas vinculadas y movimientos documentales entre diferentes oficinas.

El sistema facilita el seguimiento completo del ciclo de vida de los expedientes, desde su creación hasta su traspaso entre oficinas, manteniendo un registro detallado de todas las operaciones realizadas.

## Características Principales

### 📁 Gestión de Expedientes
- **Creación de expedientes** con códigos alfanuméricos únicos
- **Registro de observaciones** y metadatos relevantes
- **Asignación automática** de fechas de ingreso
- **Estado de digitalización** (subido a Alfresco)

### 👥 Gestión de Personas
- **Vinculación de personas** a expedientes con roles específicos:
  - Indagado
  - Víctima
  - Denunciante
  - Testigo
- **Información completa**: nombres, apellidos, documento, nacionalidad
- **Validación automática** de datos

### 🏢 Control de Movimientos
- **Registro de traspasos** entre oficinas
- **Timeline completo** del historial de movimientos
- **Responsables identificados** (entregado por/recibido por)
- **Observaciones detalladas** de cada movimiento

### 🔍 Búsqueda Avanzada
- **Búsqueda universal** por múltiples criterios:
  - Código de expediente
  - Nombres y apellidos de personas
  - Número de documento
  - Observaciones
- **Resultados paginados** con información completa
- **Vista detallada** de expedientes individuales

### 📊 Dashboard Interactivo
- **Interfaz moderna** con Vue.js
- **Navegación intuitiva** entre secciones
- **Formularios dinámicos** y validaciones en tiempo real
- **Visualización de timelines** y historiales

## Tecnologías Utilizadas

### Backend
- **Django 4.x** - Framework web Python
- **Django REST Framework** - API REST
- **SQLite** - Base de datos (desarrollo)
- **PostgreSQL** - Base de datos (producción recomendada)

### Frontend
- **Vue.js 3** - Framework JavaScript progresivo
- **HTML5/CSS3** - Estructura y estilos
- **JavaScript ES6+** - Lógica del cliente

### Infraestructura
- **Python 3.8+**
- **Pip** - Gestión de dependencias
- **Git** - Control de versiones

## Instalación

### Prerrequisitos
- Python 3.8 o superior
- Pip (gestor de paquetes de Python)
- Git

### Pasos de Instalación

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/yeti2391/app-dari.git
   cd app-dari
   ```

2. **Crear entorno virtual**
   ```bash
   python -m venv env
   # En Windows:
   env\Scripts\activate
   # En Linux/Mac:
   source env/bin/activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar la base de datos**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Crear superusuario (opcional)**
   ```bash
   python manage.py createsuperuser
   ```

6. **Ejecutar el servidor**
   ```bash
   python manage.py runserver
   ```

7. **Acceder a la aplicación**
   - Abrir navegador en: `http://localhost:8000`

## Uso

### Creación de Expedientes
1. Navegar a la sección "Crear Expediente"
2. Ingresar código único del expediente
3. Seleccionar oficina solicitante
4. Agregar observaciones iniciales
5. Confirmar creación

### Búsqueda de Información
1. Usar el campo de búsqueda principal
2. Ingresar términos de búsqueda (código, nombre, documento)
3. Revisar resultados paginados
4. Hacer clic en "Ver" para detalles completos

### Gestión de Movimientos
1. Acceder a detalles del expediente
2. Hacer clic en "Agregar Movimiento"
3. Seleccionar oficinas de origen y destino
4. Registrar responsables y observaciones
5. Confirmar el traspaso

### Vinculación de Personas
1. En la vista de detalles del expediente
2. Completar formulario de vinculación
3. Seleccionar rol de la persona
4. Confirmar la asociación

## Estructura del Proyecto

```
app-dari/
├── core/                    # Aplicación principal
│   ├── models.py           # Modelos de datos
│   ├── views.py            # Vistas y API
│   ├── urls.py             # Rutas URL
│   ├── admin.py            # Configuración admin
│   └── templates/          # Plantillas HTML
│       └── core/
│           ├── base/       # Base HTML con Vue.js
│           └── home.html   # Página principal
├── DARI/                   # Configuración del proyecto
│   ├── settings.py         # Configuración Django
│   ├── urls.py             # URLs principales
│   └── wsgi.py             # Configuración WSGI
├── static/                 # Archivos estáticos
├── db.sqlite3              # Base de datos SQLite
├── manage.py               # Script de gestión Django
└── README.md               # Este archivo
```

## API REST

La aplicación expone una API REST completa para integración con otros sistemas:

### Endpoints Principales
- `GET /api/buscar/` - Búsqueda de expedientes
- `GET /api/expediente/<id>/` - Detalles de expediente
- `POST /api/expediente/crear/` - Crear expediente
- `POST /api/movimientos/registrar/` - Registrar movimiento
- `GET /api/oficinas/` - Lista de oficinas
- `GET /api/paises/` - Lista de países

## Contribución

1. Fork el proyecto
2. Crear rama para nueva funcionalidad (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agrega nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request


## Soporte

Para soporte técnico o reportar issues, por favor crear un issue en el repositorio de GitHub.

---

**Desarrollado por:** Marco González
**Versión:** 1.0.0
**Última actualización:** Abril 2026

### Comando ejemplo para arrancar el servidor de testing: python manage.py runserver --settings=DARI.settings.testing