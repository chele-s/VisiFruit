# 🚀 VisiFruit Backend - Guía de Inicio Rápido

## 📋 Requisitos Previos

- Python 3.13+
- Entorno virtual configurado
- Archivo `.env` con configuraciones

## 🛠️ Instalación y Configuración

### 1. Verificar el Entorno Virtual
```bash
# El entorno virtual ya debe estar creado en /venv
# Si no existe, créalo con:
python -m venv venv
```

### 2. Activar el Entorno Virtual
```bash
# Windows PowerShell
& venv\Scripts\Activate.ps1

# Windows CMD
venv\Scripts\activate.bat
```

### 3. Instalar Dependencias
```bash
pip install uvicorn[standard] fastapi python-dotenv
# O si tienes requirements.txt:
pip install -r requirements.txt
```

## 🚀 Iniciar el Backend

### Opción 1: Script Automático (Recomendado)
```bash
# Ejecutar el script de inicio
start_backend.bat
```

### Opción 2: Manual
```bash
# Configurar variables de entorno
$env:PYTHONIOENCODING="utf-8"
$env:PYTHONLEGACYWINDOWSSTDIO="utf-8"
$env:FRUPRINT_ENV="development"

# Cambiar al directorio del backend
cd Interfaz_Usuario/Backend

# Iniciar el servidor
python main.py
```

## 🌐 Acceso al Sistema

Una vez iniciado, el backend estará disponible en:

- **API Principal**: http://localhost:8000
- **Dashboard/Documentación**: http://localhost:8000/docs
- **Swagger UI**: http://localhost:8000/redoc

## 📁 Estructura de Archivos

```
VisiFruit/
├── .env                     # Variables de entorno
├── start_backend.bat        # Script de inicio
├── Interfaz_Usuario/
│   └── Backend/
│       ├── main.py         # Servidor principal
│       └── backend_modules/ # Módulos del backend
├── data/                   # Base de datos SQLite
├── logs/                   # Archivos de log
└── venv/                   # Entorno virtual
```

## 🔧 Configuración del Archivo .env

El archivo `.env` debe contener las siguientes configuraciones principales:

```env
# Entorno
FRUPRINT_ENV=development
DEBUG_MODE=true
LOG_LEVEL=INFO

# Servidor
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# Base de Datos
DATABASE_URL=sqlite:///data/fruprint_ultra.db

# Configuración de Desarrollo
MOCK_HARDWARE=true
RELOAD_ON_CHANGE=true
```

## 🐛 Solución de Problemas

### Error: "ModuleNotFoundError: No module named 'uvicorn'"
```bash
pip install uvicorn[standard]
```

### Error: "database is locked"
- El sistema usa SQLite con WAL mode para permitir acceso concurrente
- Los errores de bloqueo se manejan automáticamente con reintentos

### Error: "UnicodeEncodeError" con emojis
- El sistema usa logging seguro que reemplaza emojis automáticamente
- Las variables de entorno UTF-8 están configuradas en el script

### Error: "Could not find platform independent libraries"
- Es una advertencia conocida de Python 3.13 en Windows
- No afecta la funcionalidad del sistema

## 📊 Monitoreo y Logs

- **Logs del Backend**: `logs/backend_ultra.log`
- **Logs del Sistema**: `logs/fruprint_ultra_YYYYMMDD.log`
- **Logs de Errores**: `logs/errors/errors_YYYYMMDD.log`
- **Métricas**: Disponibles en el dashboard web

## 🔄 Desarrollo

Para desarrollo, el backend incluye:

- ✅ Recarga automática de código
- ✅ Logging detallado
- ✅ Mock de hardware para pruebas
- ✅ Variables de entorno de desarrollo
- ✅ Manejo seguro de errores Unicode

## 📞 Soporte

Si encuentras problemas:

1. Revisa los logs en la carpeta `logs/`
2. Verifica que el archivo `.env` esté configurado correctamente
3. Asegúrate de que todas las dependencias estén instaladas
4. Usa el script `start_backend.bat` para un inicio automático
