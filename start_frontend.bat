@echo off
REM =============================================================================
REM Script para iniciar el Frontend React de VisiFruit
REM =============================================================================
echo.
echo ========================================
echo    VISIFRUIT FRONTEND STARTER
echo ========================================
echo.

REM Verificar que estamos en la raíz del proyecto
echo [1/6] Verificando ubicación del proyecto...
if not exist "main_etiquetadora.py" (
    echo ERROR: No estás en la raíz del proyecto VisiFruit
    echo Ejecuta este script desde la carpeta que contiene main_etiquetadora.py
    pause
    exit /b 1
)

REM Verificar que existe el directorio del frontend
echo [2/6] Verificando directorio del frontend...
if not exist "Interfaz_Usuario\VisiFruit\package.json" (
    echo ERROR: No se encontró el frontend React
    echo Verifica que existe Interfaz_Usuario/VisiFruit/
    pause
    exit /b 1
)

REM Cambiar al directorio del frontend
echo [3/6] Cambiando al directorio del frontend...
cd Interfaz_Usuario\VisiFruit

REM Verificar que Node.js está instalado
echo [4/6] Verificando Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js no está instalado
    echo Instala Node.js desde https://nodejs.org/
    pause
    exit /b 1
)

REM Verificar que las dependencias están instaladas
echo [5/6] Verificando dependencias npm...
if not exist "node_modules" (
    echo   Instalando dependencias...
    npm install
    if errorlevel 1 (
        echo ERROR: Fallo al instalar dependencias
        pause
        exit /b 1
    )
)

REM Crear archivo .env con configuración por defecto
echo [6/6] Preparando configuración...
if not exist ".env" (
    echo   Creando archivo .env...
    (
        echo # Configuración del Frontend VisiFruit
        echo # =====================================
        echo.
        echo # URLs del Backend ^(Puerto 8001 - Backend Adicional^)
        echo VITE_API_URL=http://localhost:8001
        echo VITE_WS_URL=ws://localhost:8001/ws
        echo.
        echo # Configuración de desarrollo
        echo VITE_DEV_PORT=3000
        echo VITE_ENVIRONMENT=development
        echo.
        echo # Configuración de features
        echo VITE_ENABLE_3D=true
        echo VITE_ENABLE_ANIMATIONS=true
        echo VITE_ENABLE_WEBSOCKETS=true
    ) > .env
    echo     ✅ Archivo .env creado
)

REM Iniciar el servidor de desarrollo
echo.
echo ========================================
echo    FRONTEND INICIADO EXITOSAMENTE
echo ========================================
echo.
echo Frontend disponible en: http://localhost:3000
echo Backend API: http://localhost:8001/api/docs
echo.
echo Presiona Ctrl+C para detener el servidor
echo ========================================
echo.

REM Ejecutar el frontend
npm run dev

echo.
echo ========================================
echo Frontend detenido correctamente.
echo ========================================
pause
