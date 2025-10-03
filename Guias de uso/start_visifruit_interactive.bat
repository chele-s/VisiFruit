@echo off
REM =====================================================================
REM VisiFruit - Sistema de Etiquetado Industrial
REM Launcher Interactivo con Selector de Modo
REM =====================================================================

echo.
echo =========================================================================
echo   _    ___     _______       _ __     ___     ____ _______
echo  ^| ^|  / (_)___/_  __(_)___  (_) /_   / / /   / __ `/ ___/
echo  ^| ^| / / / ___// / / / __ \/ / __/  / / /   / /_/ / __ \
echo  ^| ^|/ / (__  )/ / / / /_/ / / /_   /_/_/   \__,_/____/
echo  ^|___/_/____//_/ /_/\____/_/\__/  (_|_)
echo.
echo         Sistema de Etiquetado Industrial v4.0
echo =========================================================================
echo.

REM Activar entorno virtual si existe
if exist "venv\Scripts\activate.bat" (
    echo [+] Activando entorno virtual...
    call venv\Scripts\activate.bat
) else (
    echo [!] ADVERTENCIA: No se encontro entorno virtual
    echo [!] Ejecutando con Python del sistema...
)

echo.
echo [+] Iniciando VisiFruit...
echo.

REM Ejecutar sistema
python main_etiquetadora_v4.py

echo.
echo =========================================================================
echo Sistema finalizado
echo =========================================================================
echo.
pause

