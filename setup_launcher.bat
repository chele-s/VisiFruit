@echo off
REM =============================================================================
REM Script Maestro para configurar y compilar el VisiFruit Launcher
REM Permite elegir entre versión Python o C++ nativo
REM =============================================================================
setlocal enabledelayedexpansion
echo.
echo ========================================
echo    VISIFRUIT LAUNCHER SETUP
echo ========================================
echo.
echo Bienvenido al configurador del VisiFruit Launcher!
echo.
echo Este script te ayudará a crear un launcher visual y moderno
echo para tu sistema VisiFruit. Puedes elegir entre:
echo.
echo   1️⃣  Launcher Python (customtkinter)
echo      - Interfaz moderna y rica
echo      - Fácil de modificar
echo      - Requiere Python
echo.
echo   2️⃣  Launcher C++ Nativo
echo      - Máximo rendimiento
echo      - Inicio ultrarrápido
echo      - No requiere Python
echo.
echo   3️⃣  Ambos launchers
echo      - Lo mejor de ambos mundos
echo.
echo   4️⃣  Solo verificar dependencias
echo.
set /p choice="Elige una opción (1-4): "

if "%choice%"=="1" goto python_launcher
if "%choice%"=="2" goto cpp_launcher
if "%choice%"=="3" goto both_launchers
if "%choice%"=="4" goto check_deps
goto invalid_choice

:python_launcher
echo.
echo ========================================
echo    CONFIGURANDO LAUNCHER PYTHON
echo ========================================
echo.
call :check_python
if errorlevel 1 goto end

echo [1/4] Instalando dependencias Python...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo ERROR: Entorno virtual no encontrado
    echo Ejecuta: python -m venv venv
    goto end
)

pip install -r launcher_requirements.txt

echo.
echo [2/4] Verificando dependencias...
python -c "import customtkinter, requests" 2>nul
if errorlevel 1 (
    echo ADVERTENCIA: Algunas dependencias pueden no estar disponibles
    echo El launcher funcionará en modo básico
)

echo.
echo [3/4] Compilando a ejecutable...
python build_launcher.py --onefile --windowed --cleanup

echo.
echo [4/4] Verificando resultado...
if exist "dist\VisiFruit_Launcher.exe" (
    echo ✅ Launcher Python compilado exitosamente!
    echo 📄 Ubicación: dist\VisiFruit_Launcher.exe
) else (
    echo ❌ Error compilando launcher Python
)
goto end

:cpp_launcher
echo.
echo ========================================
echo    CONFIGURANDO LAUNCHER C++ NATIVO
echo ========================================
echo.
call :check_cpp
if errorlevel 1 goto end

echo [1/2] Compilando launcher nativo...
call compile_cpp_launcher.bat

echo.
echo [2/2] Verificando resultado...
if exist "dist_cpp\VisiFruit_Launcher_Native.exe" (
    echo ✅ Launcher C++ compilado exitosamente!
    echo 📄 Ubicación: dist_cpp\VisiFruit_Launcher_Native.exe
) else (
    echo ❌ Error compilando launcher C++
)
goto end

:both_launchers
echo.
echo ========================================
echo    CONFIGURANDO AMBOS LAUNCHERS
echo ========================================
echo.
echo Compilando versión Python...
call :python_launcher_silent

echo.
echo Compilando versión C++...
call :cpp_launcher_silent

echo.
echo ========================================
echo    RESUMEN DE COMPILACIÓN
echo ========================================
echo.
if exist "dist\VisiFruit_Launcher.exe" (
    echo ✅ Launcher Python: COMPILADO
) else (
    echo ❌ Launcher Python: ERROR
)

if exist "dist_cpp\VisiFruit_Launcher_Native.exe" (
    echo ✅ Launcher C++ Nativo: COMPILADO
) else (
    echo ❌ Launcher C++ Nativo: ERROR
)
goto end

:check_deps
echo.
echo ========================================
echo    VERIFICANDO DEPENDENCIAS
echo ========================================
echo.
call :check_python
call :check_cpp
call :check_node
call :check_project_files
goto end

:python_launcher_silent
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    pip install -r launcher_requirements.txt >nul 2>&1
    python build_launcher.py --onefile --windowed --cleanup >nul 2>&1
)
exit /b

:cpp_launcher_silent
call compile_cpp_launcher.bat >nul 2>&1
exit /b

:check_python
echo [PYTHON] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python no está instalado
    echo Descarga desde: https://www.python.org/downloads/
    exit /b 1
) else (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do (
        echo ✅ Python %%i encontrado
    )
)

if exist "venv\Scripts\python.exe" (
    echo ✅ Entorno virtual encontrado
) else (
    echo ⚠️  Entorno virtual no encontrado
    echo Ejecuta: python -m venv venv
)
exit /b 0

:check_cpp
echo [C++] Verificando compilador g++...
g++ --version >nul 2>&1
if errorlevel 1 (
    echo ❌ g++ no está instalado
    echo Instala MinGW-w64: https://www.mingw-w64.org/downloads/
    exit /b 1
) else (
    for /f "tokens=3" %%i in ('g++ --version 2^>^&1 ^| findstr "g++"') do (
        echo ✅ g++ %%i encontrado
        goto cpp_ok
    )
    :cpp_ok
)
exit /b 0

:check_node
echo [NODE] Verificando Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js no está instalado
    echo Descarga desde: https://nodejs.org/
) else (
    for /f "tokens=1" %%i in ('node --version 2^>^&1') do (
        echo ✅ Node.js %%i encontrado
    )
)
exit /b 0

:check_project_files
echo [PROYECTO] Verificando archivos del proyecto...
if exist "main_etiquetadora.py" (
    echo ✅ main_etiquetadora.py encontrado
) else (
    echo ❌ main_etiquetadora.py no encontrado
    echo ⚠️  Ejecuta este script desde la raíz del proyecto VisiFruit
)

if exist "Interfaz_Usuario\Backend\main.py" (
    echo ✅ Backend encontrado
) else (
    echo ❌ Backend no encontrado
)

if exist "Interfaz_Usuario\VisiFruit\package.json" (
    echo ✅ Frontend encontrado
) else (
    echo ❌ Frontend no encontrado
)
exit /b 0

:invalid_choice
echo.
echo ❌ Opción no válida. Por favor elige 1, 2, 3 o 4.
goto end

:end
echo.
echo ========================================
echo    CONFIGURACIÓN COMPLETADA
echo ========================================
echo.
echo 📚 Consulta README_LAUNCHER.md para más información
echo 🚀 ¡Disfruta de tu nuevo launcher visual!
echo.
pause
