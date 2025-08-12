@echo off
REM =============================================================================
REM Script para compilar el VisiFruit Launcher en C++ (Versión Nativa)
REM =============================================================================
echo.
echo ========================================
echo    COMPILADOR C++ LAUNCHER NATIVO
echo ========================================
echo.

REM Verificar que existe el archivo fuente
echo [1/4] Verificando archivo fuente...
if not exist "visifruit_launcher_cpp.cpp" (
    echo ERROR: No se encuentra visifruit_launcher_cpp.cpp
    pause
    exit /b 1
)

REM Verificar que g++ está disponible
echo [2/4] Verificando compilador g++...
g++ --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: g++ no está instalado
    echo.
    echo Instala MinGW-w64 o MSYS2:
    echo   - MinGW-w64: https://www.mingw-w64.org/downloads/
    echo   - MSYS2: https://www.msys2.org/
    echo   - O usa Visual Studio Build Tools
    echo.
    pause
    exit /b 1
)

REM Crear directorio de salida
echo [3/4] Preparando directorio de salida...
if not exist "dist_cpp" mkdir dist_cpp

REM Compilar el launcher
echo [4/4] Compilando launcher nativo...
echo.
echo Compilando con optimizaciones...

g++ -std=c++17 ^
    -static ^
    -O3 ^
    -s ^
    -mwindows ^
    visifruit_launcher_cpp.cpp ^
    -o dist_cpp\VisiFruit_Launcher_Native.exe ^
    -lcomctl32 ^
    -lshell32 ^
    -luser32 ^
    -lkernel32 ^
    -lgdi32 ^
    -lws2_32 ^
    -lwininet

if errorlevel 1 (
    echo.
    echo ERROR: Fallo la compilación
    echo Revisa los errores anteriores
    pause
    exit /b 1
)

echo.
echo ========================================
echo    COMPILACIÓN EXITOSA
echo ========================================
echo.
echo Ejecutable generado: dist_cpp\VisiFruit_Launcher_Native.exe
echo.

REM Mostrar información del archivo
for %%I in (dist_cpp\VisiFruit_Launcher_Native.exe) do (
    set size=%%~zI
    set /a size_kb=!size!/1024
    echo Tamaño: !size_kb! KB
)

echo.
echo Características del launcher nativo:
echo   ✅ Interfaz nativa de Windows
echo   ✅ Inicio ultrarrápido
echo   ✅ Bajo consumo de memoria
echo   ✅ No requiere Python instalado
echo   ✅ Ejecutable totalmente independiente
echo.
echo Para usar:
echo   1. Ve a la carpeta 'dist_cpp'
echo   2. Ejecuta 'VisiFruit_Launcher_Native.exe'
echo   3. ¡Disfruta del máximo rendimiento!
echo.
pause
