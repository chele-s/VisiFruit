@echo off
REM =============================================================================
REM Script para iniciar el backend de VisiFruit con configuración completa
REM =============================================================================
echo.
echo ========================================
echo    VISIFRUIT BACKEND STARTER
echo ========================================
echo.

REM Configurar variables de entorno para UTF-8
echo [1/7] Configurando variables de entorno...
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSSTDIO=utf-8
set PYTHONPATH=%CD%
set FRUPRINT_ENV=development

REM Verificar que el archivo .env existe
echo [2/7] Verificando archivo .env...
if not exist ".env" (
    echo ERROR: Archivo .env no encontrado
    echo Crea el archivo .env con las configuraciones necesarias
    pause
    exit /b 1
)

REM Activar entorno virtual
echo [3/7] Activando entorno virtual...
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Entorno virtual no encontrado
    echo Ejecuta: python -m venv venv
    pause
    exit /b 1
)
call venv\Scripts\activate.bat

REM Verificar que las dependencias están instaladas
echo [4/7] Verificando dependencias...
python -c "import uvicorn, fastapi" 2>nul
if errorlevel 1 (
    echo ERROR: Dependencias no instaladas
    echo Ejecuta: pip install -r requirements.txt
    pause
    exit /b 1
)

REM Verificar puertos disponibles
echo [5/7] Verificando puertos disponibles...
python check_ports.py
if errorlevel 1 (
    echo.
    echo ADVERTENCIA: Algunos puertos pueden estar ocupados
    echo Revisa el resultado anterior y resuelve conflictos si es necesario
    echo.
    pause
)

REM Cambiar al directorio del backend
echo [6/7] Cambiando al directorio del backend...
cd Interfaz_Usuario\Backend

REM Iniciar el backend
echo [7/7] Iniciando servidor backend...
echo.
echo Backend disponible en: http://localhost:8001
echo Dashboard API: http://localhost:8001/docs
echo.
echo Presiona Ctrl+C para detener el servidor
echo.
python main.py

echo.
echo Backend detenido.
pause
