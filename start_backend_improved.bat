@echo off
REM =============================================================================
REM Script mejorado para iniciar el backend de VisiFruit
REM =============================================================================
echo.
echo ========================================
echo    VISIFRUIT BACKEND STARTER v2.0
echo ========================================
echo.

REM Verificar que estamos en la raíz del proyecto
echo [1/8] Verificando ubicación del proyecto...
if not exist "main_etiquetadora.py" (
    echo ERROR: No estás en la raíz del proyecto VisiFruit
    echo Ejecuta este script desde la carpeta que contiene main_etiquetadora.py
    pause
    exit /b 1
)

REM Configurar variables de entorno para UTF-8
echo [2/8] Configurando variables de entorno...
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSSTDIO=utf-8
set PYTHONPATH=%CD%
set FRUPRINT_ENV=development

REM Activar entorno virtual
echo [3/8] Activando entorno virtual...
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Entorno virtual no encontrado
    echo Ejecuta: python -m venv venv
    pause
    exit /b 1
)
call venv\Scripts\activate.bat

REM Verificar que las dependencias están instaladas
echo [4/8] Verificando dependencias principales...
python -c "import uvicorn, fastapi" 2>nul
if errorlevel 1 (
    echo ERROR: Dependencias no instaladas
    echo Ejecuta: pip install -r requirements.txt
    pause
    exit /b 1
)

REM Verificar puertos disponibles
echo [5/8] Verificando puertos disponibles...
python check_ports.py
if errorlevel 1 (
    echo.
    echo ADVERTENCIA: Algunos puertos pueden estar ocupados
    echo Revisa el resultado anterior y resuelve conflictos si es necesario
    echo.
    set /p continue="¿Continuar de todos modos? (S/N): "
    if /i not "!continue!"=="S" if /i not "!continue!"=="Y" (
        echo Operación cancelada por el usuario
        pause
        exit /b 1
    )
)

REM Crear directorios necesarios
echo [6/8] Preparando directorios...
if not exist "Interfaz_Usuario\Backend\logs" (
    mkdir "Interfaz_Usuario\Backend\logs"
    echo   - Creado directorio logs/
)

REM Cambiar al directorio del backend
echo [7/8] Cambiando al directorio del backend...
cd Interfaz_Usuario\Backend

REM Iniciar el backend
echo [8/8] Iniciando servidor backend...
echo.
echo ========================================
echo    BACKEND INICIADO EXITOSAMENTE
echo ========================================
echo.
echo Backend disponible en: http://localhost:8001
echo Dashboard API: http://localhost:8001/api/docs
echo WebSocket realtime: ws://localhost:8001/ws/realtime
echo WebSocket dashboard: ws://localhost:8001/ws/dashboard
echo.
echo Presiona Ctrl+C para detener el servidor
echo ========================================
echo.

REM Ejecutar el backend
python main.py

echo.
echo ========================================
echo Backend detenido correctamente.
echo ========================================
pause
