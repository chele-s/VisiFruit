@echo off
REM =============================================================================
REM Script simplificado para compilar el launcher completo
REM =============================================================================
echo.
echo ========================================
echo    COMPILADOR LAUNCHER COMPLETO
echo ========================================
echo.

REM Activar entorno virtual
call venv\Scripts\activate.bat

REM Configurar variables de entorno para Tcl/Tk
echo [1/4] Configurando variables de entorno...
set PYTHON_ROOT=C:\Users\DELL\AppData\Local\Programs\Python\Python313
set TCL_LIBRARY=%PYTHON_ROOT%\tcl\tcl8.6
set TK_LIBRARY=%PYTHON_ROOT%\tcl\tk8.6

echo   TCL_LIBRARY configurado
echo   TK_LIBRARY configurado

REM Instalar dependencias
echo [2/4] Verificando dependencias...
pip install -r launcher_requirements.txt >nul 2>&1

REM Probar tkinter
echo [3/4] Probando compatibilidad...
python -c "import tkinter; print('tkinter OK')" 2>nul
if errorlevel 1 (
    echo   ⚠️ tkinter con problemas, usando launcher fixed
    set LAUNCHER_FILE=visifruit_launcher_fixed.py
) else (
    echo   ✅ tkinter funcionando
    set LAUNCHER_FILE=visifruit_launcher.py
)

REM Compilar
echo [4/4] Compilando launcher completo...
echo.
echo Compilando %LAUNCHER_FILE%...

pyinstaller --name="VisiFruit_Launcher_Complete" --onefile --windowed --add-data "start_sistema_completo.bat;." --add-data "start_sistema_completo.ps1;." --add-data "start_backend.bat;." --add-data "start_frontend.bat;." --distpath="dist_complete" --workpath="build_temp" --specpath="build_specs" --hidden-import="tkinter" --hidden-import="customtkinter" --hidden-import="requests" %LAUNCHER_FILE%

if errorlevel 1 (
    echo.
    echo ❌ Error en la compilación
    echo Intentando con configuración alternativa...
    echo.
    
    REM Intentar sin --windowed para ver errores
    pyinstaller --name="VisiFruit_Launcher_Complete_Debug" --onefile --add-data "start_sistema_completo.bat;." --distpath="dist_complete" %LAUNCHER_FILE%
    
    if errorlevel 1 (
        echo ❌ Compilación fallida completamente
        pause
        exit /b 1
    )
)

echo.
echo ========================================
echo    RESULTADO
echo ========================================
echo.

if exist "dist_complete\VisiFruit_Launcher_Complete.exe" (
    echo ✅ ÉXITO: Launcher completo compilado
    echo.
    echo 📄 Ubicación: dist_complete\VisiFruit_Launcher_Complete.exe
    echo.
    for %%I in (dist_complete\VisiFruit_Launcher_Complete.exe) do (
        set size=%%~zI
        set /a size_mb=!size!/1048576
        echo 📊 Tamaño: !size_mb! MB
    )
    echo.
    echo PARA USAR:
    echo   1. Ve a la carpeta 'dist_complete'
    echo   2. Ejecuta 'VisiFruit_Launcher_Complete.exe'
    echo   3. ¡Disfruta tu launcher visual completo!
    echo.
) else if exist "dist_complete\VisiFruit_Launcher_Complete_Debug.exe" (
    echo ✅ ÉXITO: Launcher compilado (versión debug)
    echo.
    echo 📄 Ubicación: dist_complete\VisiFruit_Launcher_Complete_Debug.exe
    echo.
    echo NOTA: Esta versión muestra la consola para debugging
    echo.
) else (
    echo ❌ No se pudo crear el ejecutable
    echo.
    echo ALTERNATIVAS:
    echo 1. Usar: python visifruit_launcher_fixed.py
    echo 2. Usar: python visifruit_launcher_simple.py
    echo 3. Usar: .\start_sistema_completo.bat
    echo.
)

echo.
pause
