@echo off
REM =============================================================================
REM Script para ejecutar el VisiFruit Launcher desde cualquier ubicación
REM =============================================================================
echo.
echo ========================================
echo    VISIFRUIT LAUNCHER EJECUTOR
echo ========================================
echo.

REM Verificar que estamos en la raíz del proyecto
if not exist "main_etiquetadora.py" (
    echo ❌ ERROR: Este script debe ejecutarse desde la raíz del proyecto VisiFruit
    echo    Asegúrate de estar en la carpeta que contiene main_etiquetadora.py
    echo.
    pause
    exit /b 1
)

echo 🔍 Detectando launchers disponibles...
echo.

REM Verificar qué launchers están disponibles
set LAUNCHER_FOUND=0

if exist "dist_final\VisiFruit_Launcher.exe" (
    echo ✅ Launcher Principal encontrado: dist_final\VisiFruit_Launcher.exe
    set LAUNCHER_MAIN=dist_final\VisiFruit_Launcher.exe
    set LAUNCHER_FOUND=1
)

if exist "dist_complete\VisiFruit_Launcher_Complete_Debug.exe" (
    echo ✅ Launcher Debug encontrado: dist_complete\VisiFruit_Launcher_Complete_Debug.exe
    set LAUNCHER_DEBUG=dist_complete\VisiFruit_Launcher_Complete_Debug.exe
    set LAUNCHER_FOUND=1
)

if exist "visifruit_launcher_fixed.py" (
    echo ✅ Launcher Python encontrado: visifruit_launcher_fixed.py
    set LAUNCHER_PYTHON=visifruit_launcher_fixed.py
    set LAUNCHER_FOUND=1
)

if exist "visifruit_launcher_simple.py" (
    echo ✅ Launcher Simple encontrado: visifruit_launcher_simple.py
    set LAUNCHER_SIMPLE=visifruit_launcher_simple.py
    set LAUNCHER_FOUND=1
)

echo.

if %LAUNCHER_FOUND%==0 (
    echo ❌ No se encontraron launchers compilados
    echo.
    echo Para compilar el launcher ejecuta:
    echo   1. .\setup_launcher.bat
    echo   2. O .\build_complete_launcher.bat
    echo.
    pause
    exit /b 1
)

echo ========================================
echo    SELECCIONA TU LAUNCHER PREFERIDO
echo ========================================
echo.

set MENU_OPTIONS=0

if defined LAUNCHER_MAIN (
    set /a MENU_OPTIONS+=1
    echo %MENU_OPTIONS%. 🚀 Launcher Principal (Recomendado)
    echo    - Interfaz moderna sin consola
    echo    - Archivo: %LAUNCHER_MAIN%
    echo.
)

if defined LAUNCHER_DEBUG (
    set /a MENU_OPTIONS+=1
    echo %MENU_OPTIONS%. 🔧 Launcher Debug
    echo    - Interfaz moderna con consola (para debugging)
    echo    - Archivo: %LAUNCHER_DEBUG%
    echo.
)

if defined LAUNCHER_PYTHON (
    set /a MENU_OPTIONS+=1
    echo %MENU_OPTIONS%. 🐍 Launcher Python
    echo    - Requiere Python instalado
    echo    - Archivo: %LAUNCHER_PYTHON%
    echo.
)

if defined LAUNCHER_SIMPLE (
    set /a MENU_OPTIONS+=1
    echo %MENU_OPTIONS%. 📝 Launcher Simple (Línea de comandos)
    echo    - Sin GUI, solo texto
    echo    - Archivo: %LAUNCHER_SIMPLE%
    echo.
)

set /a MENU_OPTIONS+=1
echo %MENU_OPTIONS%. ❌ Salir

echo.
set /p choice="Elige una opción (1-%MENU_OPTIONS%): "

REM Procesar selección
set CURRENT_OPTION=0

if defined LAUNCHER_MAIN (
    set /a CURRENT_OPTION+=1
    if "%choice%"=="%CURRENT_OPTION%" (
        echo.
        echo 🚀 Iniciando Launcher Principal...
        echo.
        start "" "%LAUNCHER_MAIN%"
        echo ✅ Launcher iniciado exitosamente
        echo 💡 El launcher se abrirá en una ventana separada
        goto success
    )
)

if defined LAUNCHER_DEBUG (
    set /a CURRENT_OPTION+=1
    if "%choice%"=="%CURRENT_OPTION%" (
        echo.
        echo 🔧 Iniciando Launcher Debug...
        echo.
        start "" "%LAUNCHER_DEBUG%"
        echo ✅ Launcher debug iniciado exitosamente
        echo 💡 El launcher se abrirá con consola para debugging
        goto success
    )
)

if defined LAUNCHER_PYTHON (
    set /a CURRENT_OPTION+=1
    if "%choice%"=="%CURRENT_OPTION%" (
        echo.
        echo 🐍 Iniciando Launcher Python...
        
        if exist "venv\Scripts\activate.bat" (
            echo   Activando entorno virtual...
            call venv\Scripts\activate.bat
        )
        
        echo   Ejecutando launcher...
        python "%LAUNCHER_PYTHON%"
        goto success
    )
)

if defined LAUNCHER_SIMPLE (
    set /a CURRENT_OPTION+=1
    if "%choice%"=="%CURRENT_OPTION%" (
        echo.
        echo 📝 Iniciando Launcher Simple...
        
        if exist "venv\Scripts\activate.bat" (
            echo   Activando entorno virtual...
            call venv\Scripts\activate.bat
        )
        
        echo   Ejecutando launcher simple...
        python "%LAUNCHER_SIMPLE%"
        goto success
    )
)

set /a CURRENT_OPTION+=1
if "%choice%"=="%CURRENT_OPTION%" (
    echo.
    echo 👋 ¡Hasta luego!
    goto end
)

echo.
echo ❌ Opción no válida: %choice%
echo.
pause
goto end

:success
echo.
echo ========================================
echo    LAUNCHER EJECUTADO EXITOSAMENTE
echo ========================================
echo.
echo 💡 CONSEJOS:
echo   - Si es tu primera vez, usa "🚀 Iniciar Sistema Completo"
echo   - Los indicadores te muestran el estado en tiempo real
echo   - Usa los enlaces rápidos para abrir URLs
echo.

:end
echo.
pause
