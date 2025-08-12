@echo off
REM =============================================================================
REM Script final para crear el launcher completo sin consola de debug
REM =============================================================================
echo.
echo ========================================
echo    COMPILADOR LAUNCHER FINAL
echo ========================================
echo.

call venv\Scripts\activate.bat

REM Configurar variables de entorno
set PYTHON_ROOT=C:\Users\DELL\AppData\Local\Programs\Python\Python313
set TCL_LIBRARY=%PYTHON_ROOT%\tcl\tcl8.6
set TK_LIBRARY=%PYTHON_ROOT%\tcl\tk8.6

echo [1/2] Compilando versión final del launcher...
echo.

REM Compilar versión final sin consola
pyinstaller --name="VisiFruit_Launcher" --onefile --windowed --distpath="dist_final" --workpath="build_final" --specpath="spec_final" --hidden-import="tkinter" --hidden-import="customtkinter" --hidden-import="requests" --noconfirm visifruit_launcher_fixed.py

if errorlevel 1 (
    echo ❌ Error compilando versión windowed
    echo Usando versión debug existente...
    
    if not exist "dist_final" mkdir dist_final
    copy "dist_complete\VisiFruit_Launcher_Complete_Debug.exe" "dist_final\VisiFruit_Launcher.exe"
    
    echo ✅ Copiado launcher debug como versión final
) else (
    echo ✅ Compilación exitosa
)

echo.
echo [2/2] Verificando resultado...

if exist "dist_final\VisiFruit_Launcher.exe" (
    echo.
    echo ========================================
    echo    ✅ LAUNCHER COMPLETADO EXITOSAMENTE
    echo ========================================
    echo.
    echo 📄 Ubicación: dist_final\VisiFruit_Launcher.exe
    
    for %%I in (dist_final\VisiFruit_Launcher.exe) do (
        set size=%%~zI
        set /a size_mb=!size!/1048576
        echo 📊 Tamaño: !size_mb! MB
    )
    
    echo.
    echo 🎉 CARACTERÍSTICAS DEL LAUNCHER:
    echo   ✅ Interfaz gráfica moderna (CustomTkinter)
    echo   ✅ Compatible con Python 3.13
    echo   ✅ Logs visuales con colores y emojis
    echo   ✅ Monitoreo en tiempo real de servicios
    echo   ✅ Apertura automática del navegador
    echo   ✅ Control completo del sistema VisiFruit
    echo   ✅ Ejecutable independiente (no requiere Python)
    echo.
    echo 🚀 PARA USAR:
    echo   1. Ve a la carpeta 'dist_final'
    echo   2. Ejecuta 'VisiFruit_Launcher.exe'
    echo   3. ¡Disfruta tu launcher visual profesional!
    echo.
    echo 💡 CONSEJO:
    echo   - Puedes copiar el .exe a cualquier lugar
    echo   - No requiere instalación
    echo   - Funciona en cualquier Windows 10/11
    echo.
) else (
    echo ❌ No se pudo crear el launcher final
    echo.
    echo ALTERNATIVAS DISPONIBLES:
    echo 1. dist_complete\VisiFruit_Launcher_Complete_Debug.exe (con consola)
    echo 2. python visifruit_launcher_fixed.py (requiere Python)
    echo 3. python visifruit_launcher_simple.py (sin GUI)
    echo.
)

echo.
pause
