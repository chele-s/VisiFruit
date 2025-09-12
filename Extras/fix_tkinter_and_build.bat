@echo off
REM =============================================================================
REM Script para arreglar Tcl/Tk en Python 3.13 y compilar el launcher completo
REM =============================================================================
echo.
echo ========================================
echo    REPARADOR Y COMPILADOR LAUNCHER
echo ========================================
echo.

REM Activar entorno virtual
echo [1/6] Activando entorno virtual...
call venv\Scripts\activate.bat

REM Configurar variables de entorno para Tcl/Tk
echo [2/6] Configurando variables de entorno Tcl/Tk...
set PYTHON_ROOT=C:\Users\DELL\AppData\Local\Programs\Python\Python313
set TCL_LIBRARY=%PYTHON_ROOT%\tcl\tcl8.6
set TK_LIBRARY=%PYTHON_ROOT%\tcl\tk8.6

echo   TCL_LIBRARY=%TCL_LIBRARY%
echo   TK_LIBRARY=%TK_LIBRARY%

REM Verificar directorios Tcl
echo [3/6] Verificando directorios Tcl...
if exist "%TCL_LIBRARY%" (
    echo   ✅ Directorio Tcl encontrado
) else (
    echo   ❌ Directorio Tcl no encontrado
    echo   Buscando ubicaciones alternativas...
    
    REM Buscar en otras ubicaciones comunes
    for %%D in (
        "%PYTHON_ROOT%\Lib\tcl8.6"
        "%PYTHON_ROOT%\libs\tcl8.6"
        "%PYTHON_ROOT%\tcl"
    ) do (
        if exist "%%D" (
            set TCL_LIBRARY=%%D
            echo   ✅ Tcl encontrado en: %%D
            goto tcl_found
        )
    )
    
    echo   ⚠️ Tcl no encontrado, continuando con compilación...
    :tcl_found
)

REM Instalar todas las dependencias
echo [4/6] Instalando dependencias...
pip install -r launcher_requirements.txt

REM Verificar que tkinter funciona
echo [5/6] Probando tkinter...
python -c "import tkinter; print('✅ tkinter funciona')" 2>nul
if errorlevel 1 (
    echo   ⚠️ tkinter aún tiene problemas, pero intentaremos compilar
) else (
    echo   ✅ tkinter funciona correctamente
)

REM Compilar el launcher con PyInstaller
echo [6/6] Compilando launcher completo...
echo.
echo Usando PyInstaller con configuración optimizada para Python 3.13...

pyinstaller ^
    --name="VisiFruit_Launcher_Complete" ^
    --onefile ^
    --windowed ^
    --add-data "start_sistema_completo.bat;." ^
    --add-data "start_sistema_completo.ps1;." ^
    --add-data "start_backend.bat;." ^
    --add-data "start_frontend.bat;." ^
    --add-data "launcher_requirements.txt;." ^
    --distpath="dist_complete" ^
    --workpath="build_temp_complete" ^
    --specpath="build_specs_complete" ^
    --hidden-import="tkinter" ^
    --hidden-import="tkinter.ttk" ^
    --hidden-import="customtkinter" ^
    --hidden-import="requests" ^
    --collect-all="customtkinter" ^
    --collect-all="tkinter" ^
    visifruit_launcher.py

if errorlevel 1 (
    echo.
    echo ❌ Error durante la compilación
    echo.
    echo POSIBLES SOLUCIONES:
    echo 1. Reinstalar Python 3.12 (más estable que 3.13)
    echo 2. Usar el launcher simple: python build_launcher.py --simple
    echo 3. Usar directamente: python visifruit_launcher_simple.py
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo    COMPILACIÓN EXITOSA
echo ========================================
echo.

if exist "dist_complete\VisiFruit_Launcher_Complete.exe" (
    echo ✅ Launcher completo compilado exitosamente!
    echo.
    echo 📄 Ubicación: dist_complete\VisiFruit_Launcher_Complete.exe
    echo.
    echo CARACTERÍSTICAS:
    echo   ✅ Interfaz gráfica moderna (CustomTkinter)
    echo   ✅ Logs visuales con colores
    echo   ✅ Monitoreo en tiempo real
    echo   ✅ Apertura automática del navegador
    echo   ✅ Ejecutable independiente
    echo.
    echo Para usar:
    echo   1. Ve a la carpeta 'dist_complete'
    echo   2. Ejecuta 'VisiFruit_Launcher_Complete.exe'
    echo   3. ¡Disfruta tu launcher visual completo!
    echo.
) else (
    echo ❌ No se pudo crear el ejecutable
    echo Revisa los errores anteriores
)

echo.
pause
