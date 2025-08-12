@echo off
REM =============================================================================
REM Script maestro para iniciar el Sistema Completo VisiFruit
REM Backend (Puerto 8001) + Frontend (Puerto 3000)
REM =============================================================================
echo.
echo ================================================
echo    VISIFRUIT SISTEMA COMPLETO v3.0
echo ================================================
echo.

REM Verificar ubicación
echo [1/8] Verificando ubicación del proyecto...
if not exist "main_etiquetadora.py" (
    echo ERROR: No estás en la raíz del proyecto VisiFruit
    echo Ejecuta este script desde la carpeta que contiene main_etiquetadora.py
    pause
    exit /b 1
)

REM Configurar variables de entorno
echo [2/8] Configurando variables de entorno...
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSSTDIO=utf-8
set PYTHONPATH=%CD%
set FRUPRINT_ENV=development

REM Verificar entorno virtual Python
echo [3/8] Verificando entorno virtual Python...
if not exist "venv\Scripts\python.exe" (
    echo ERROR: Entorno virtual no encontrado
    echo Ejecuta: python -m venv venv
    pause
    exit /b 1
)

REM Verificar Node.js
echo [4/8] Verificando Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js no está instalado
    echo Instala Node.js desde https://nodejs.org/
    pause
    exit /b 1
)

REM Verificar puertos disponibles
echo [5/8] Verificando puertos disponibles...
call venv\Scripts\activate.bat
python check_ports.py
if errorlevel 1 (
    echo.
    echo ADVERTENCIA: Algunos puertos pueden estar ocupados
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
)

REM Preparar frontend
echo [7/8] Preparando frontend React...
cd Interfaz_Usuario\VisiFruit

REM Instalar dependencias si no existen
if not exist "node_modules" (
    echo   Instalando dependencias npm...
    npm install --silent
    if errorlevel 1 (
        echo ERROR: Fallo instalación npm
        cd ..\..
        pause
        exit /b 1
    )
)

REM Crear .env para frontend si no existe
if not exist ".env" (
    echo   Creando configuración frontend...
    (
        echo # Configuración del Frontend VisiFruit
        echo VITE_API_URL=http://localhost:8001
        echo VITE_WS_URL=ws://localhost:8001/ws/realtime
        echo VITE_DEV_PORT=3000
        echo VITE_ENVIRONMENT=development
        echo VITE_ENABLE_3D=true
        echo VITE_ENABLE_ANIMATIONS=true
        echo VITE_ENABLE_WEBSOCKETS=true
    ) > .env
)

cd ..\..

REM Iniciar servicios
echo [8/8] Iniciando servicios...
echo.
echo ================================================
echo    SISTEMA INICIADO EXITOSAMENTE
echo ================================================
echo.
echo 🟢 Backend API:     http://localhost:8001
echo 🟢 Dashboard API:   http://localhost:8001/api/docs
echo 🟢 Frontend React:  http://localhost:3000
echo 🟢 WebSocket:       ws://localhost:8001/ws
echo.
echo ⚠️  IMPORTANTE:
echo    - Backend se iniciará en ventana 1
echo    - Frontend se iniciará en ventana 2
echo    - Cierra ambas ventanas para detener
echo ================================================
echo.

REM Iniciar backend en ventana separada
start "VisiFruit Backend" cmd /c "call venv\Scripts\activate.bat && cd Interfaz_Usuario\Backend && python main.py && pause"

REM Esperar 3 segundos para que el backend inicie
echo Esperando que el backend inicie...
timeout /t 3 /nobreak >nul

REM Iniciar frontend en ventana separada
start "VisiFruit Frontend" cmd /c "cd Interfaz_Usuario\VisiFruit && npm run dev"

echo.
echo ================================================
echo Sistema completo iniciado exitosamente!
echo.
echo Para detener:
echo   - Cierra la ventana "VisiFruit Backend"
echo   - Cierra la ventana "VisiFruit Frontend"  
echo   - O presiona Ctrl+C en ambas ventanas
echo ================================================
echo.

REM Mantener ventana principal abierta
echo Presiona cualquier tecla para cerrar esta ventana...
echo (El sistema seguirá ejecutándose en las otras ventanas)
pause >nul
