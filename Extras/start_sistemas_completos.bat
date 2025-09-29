@echo off
REM ============================================================================
REM Script de Inicio Completo - VisiFruit
REM ============================================================================
REM Inicia todos los sistemas necesarios para el control de banda:
REM - Sistema Principal (puerto 8000)
REM - Sistema Demo (puerto 8002)
REM - Backend UI (puerto 8001)
REM - Frontend React (puerto 5173)
REM ============================================================================

echo.
echo ========================================================================
echo   🚀 VisiFruit - Inicio de Sistemas Completos
echo ========================================================================
echo.

cd /d "%~dp0.."

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Python no está instalado o no está en PATH
    pause
    exit /b 1
)

echo ✅ Python encontrado
echo.

REM Crear directorio de logs si no existe
if not exist "logs" mkdir logs

echo 📋 Selecciona qué sistemas deseas iniciar:
echo.
echo [1] Sistema Principal (puerto 8000) - Versión profesional
echo [2] Sistema Demo (puerto 8002) - Versión prototipo/demo
echo [3] Ambos sistemas
echo [4] Todo (Sistemas + Backend UI + Frontend)
echo.

set /p choice="Tu elección (1-4): "

if "%choice%"=="1" goto start_main
if "%choice%"=="2" goto start_demo
if "%choice%"=="3" goto start_both
if "%choice%"=="4" goto start_all
goto invalid_choice

:start_main
echo.
echo 🎯 Iniciando Sistema Principal...
echo.
start "VisiFruit - Sistema Principal (8000)" cmd /k "python main_etiquetadora_v4.py"
timeout /t 3 >nul
echo ✅ Sistema Principal iniciado en http://localhost:8000
goto end

:start_demo
echo.
echo 🎮 Iniciando Sistema Demo...
echo.
start "VisiFruit - Sistema Demo (8002)" cmd /k "python Control_Etiquetado\demo_sistema_web_server.py"
timeout /t 3 >nul
echo ✅ Sistema Demo iniciado en http://localhost:8002
goto end

:start_both
echo.
echo 🔄 Iniciando ambos sistemas...
echo.
start "VisiFruit - Sistema Principal (8000)" cmd /k "python main_etiquetadora_v4.py"
timeout /t 2 >nul
start "VisiFruit - Sistema Demo (8002)" cmd /k "python Control_Etiquetado\demo_sistema_web_server.py"
timeout /t 3 >nul
echo ✅ Ambos sistemas iniciados:
echo    - Principal: http://localhost:8000
echo    - Demo: http://localhost:8002
goto end

:start_all
echo.
echo 🚀 Iniciando TODOS los servicios...
echo.

REM Sistema Principal
echo [1/4] Iniciando Sistema Principal...
start "VisiFruit - Sistema Principal (8000)" cmd /k "python main_etiquetadora_v4.py"
timeout /t 2 >nul

REM Sistema Demo
echo [2/4] Iniciando Sistema Demo...
start "VisiFruit - Sistema Demo (8002)" cmd /k "python Control_Etiquetado\demo_sistema_web_server.py"
timeout /t 2 >nul

REM Backend UI
echo [3/4] Iniciando Backend UI...
cd Interfaz_Usuario\Backend
start "VisiFruit - Backend UI (8001)" cmd /k "python main.py"
cd ..\..
timeout /t 3 >nul

REM Frontend React
echo [4/4] Iniciando Frontend React...
cd Interfaz_Usuario\VisiFruit
if exist "node_modules" (
    start "VisiFruit - Frontend (5173)" cmd /k "npm run dev"
) else (
    echo ⚠️  Advertencia: node_modules no encontrado
    echo    Ejecuta 'npm install' primero en Interfaz_Usuario\VisiFruit
)
cd ..\..

timeout /t 3 >nul
echo.
echo ✅ Todos los servicios iniciados:
echo    - Sistema Principal: http://localhost:8000
echo    - Sistema Demo: http://localhost:8002
echo    - Backend UI: http://localhost:8001
echo    - Frontend: http://localhost:5173
echo.
echo 💡 Abre tu navegador en: http://localhost:5173
goto end

:invalid_choice
echo.
echo ❌ Opción inválida. Por favor elige 1, 2, 3 o 4.
pause
exit /b 1

:end
echo.
echo ========================================================================
echo   ✅ Sistemas iniciados correctamente
echo ========================================================================
echo.
echo 📖 Para probar la integración, ejecuta:
echo    python Extras\test_belt_integration.py
echo.
echo 🌐 Accede a la interfaz web:
echo    http://localhost:5173
echo.
echo 📚 Documentación:
echo    Guias de uso\INTEGRACION_FRONTEND_BANDA.md
echo.
pause
