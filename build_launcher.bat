@echo off
REM =============================================================================
REM Script para compilar el VisiFruit Launcher a .exe
REM =============================================================================
echo.
echo ========================================
echo    VISIFRUIT LAUNCHER BUILDER
echo ========================================
echo.

REM Verificar que estamos en la ubicación correcta
echo [1/6] Verificando ubicación...
if not exist "visifruit_launcher.py" (
    echo ERROR: No se encuentra visifruit_launcher.py
    echo Ejecuta este script desde la raíz del proyecto
    pause
    exit /b 1
)

REM Verificar entorno virtual
echo [2/6] Verificando entorno virtual...
if not exist "venv\Scripts\python.exe" (
    echo ERROR: Entorno virtual no encontrado
    echo Ejecuta: python -m venv venv
    pause
    exit /b 1
)

REM Activar entorno virtual
echo [3/6] Activando entorno virtual...
call venv\Scripts\activate.bat

REM Instalar dependencias del launcher
echo [4/6] Instalando dependencias del launcher...
pip install -r launcher_requirements.txt

REM Verificar PyInstaller
echo [5/6] Verificando PyInstaller...
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo ERROR: PyInstaller no está instalado
    echo Instalando PyInstaller...
    pip install pyinstaller
)

REM Compilar el launcher
echo [6/6] Compilando launcher...
echo.
echo Selecciona el tipo de compilación:
echo [1] Un solo archivo .exe (recomendado para distribución)
echo [2] Carpeta con archivos (inicio más rápido)
echo [3] Con ventana de consola (para debugging)
echo.
set /p choice="Elige una opción (1-3): "

if "%choice%"=="1" (
    echo Compilando como archivo único...
    python build_launcher.py --onefile --windowed --cleanup
) else if "%choice%"=="2" (
    echo Compilando como carpeta...
    python build_launcher.py --windowed --cleanup
) else if "%choice%"=="3" (
    echo Compilando con consola de debug...
    python build_launcher.py --debug --cleanup
) else (
    echo Opción no válida. Usando configuración por defecto...
    python build_launcher.py --onefile --windowed --cleanup
)

echo.
echo ========================================
echo    COMPILACIÓN COMPLETADA
echo ========================================
echo.
echo El ejecutable se encuentra en la carpeta 'dist'
echo.
echo Para usar:
echo   1. Ve a la carpeta 'dist'
echo   2. Ejecuta 'VisiFruit_Launcher.exe'
echo   3. ¡Disfruta tu launcher visual!
echo.
pause
