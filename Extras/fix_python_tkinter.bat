@echo off
REM =============================================================================
REM Script para arreglar el problema de Tcl/Tk en Python 3.13 en Windows
REM =============================================================================
echo.
echo ========================================
echo    REPARADOR DE PYTHON TKINTER
echo ========================================
echo.
echo El error de "Can't find a usable init.tcl" es común en Python 3.13.
echo Este script intentará solucionarlo.
echo.

REM Opción 1: Verificar variables de entorno
echo [1/4] Verificando variables de entorno...
set PYTHON_DIR=C:\Users\DELL\AppData\Local\Programs\Python\Python313
if exist "%PYTHON_DIR%\tcl\tcl8.6" (
    echo ✅ Encontrado directorio tcl
    set TCL_LIBRARY=%PYTHON_DIR%\tcl\tcl8.6
    set TK_LIBRARY=%PYTHON_DIR%\tcl\tk8.6
    echo   TCL_LIBRARY=%TCL_LIBRARY%
    echo   TK_LIBRARY=%TK_LIBRARY%
) else (
    echo ❌ No se encontró directorio tcl en %PYTHON_DIR%
)

REM Opción 2: Reinstalar tkinter
echo.
echo [2/4] Verificando instalación de tkinter...
python -c "import tkinter; print('✅ tkinter funciona')" 2>nul
if errorlevel 1 (
    echo ❌ tkinter no funciona
    echo.
    echo SOLUCIONES RECOMENDADAS:
    echo.
    echo 1. Reinstalar Python desde python.org con "Add Python to PATH" marcado
    echo 2. Durante la instalación, marcar "tcl/tk and IDLE" 
    echo 3. O descargar Python desde Microsoft Store
    echo.
    echo URLs útiles:
    echo   - Python oficial: https://www.python.org/downloads/
    echo   - Microsoft Store: ms-windows-store://pdp/?productid=9NCVDN91XZQP
    echo.
) else (
    echo ✅ tkinter está instalado pero puede tener problemas de configuración
)

REM Opción 3: Crear variables de entorno temporales
echo.
echo [3/4] Intentando configuración temporal...
echo Creando script de inicio con variables de entorno...

(
echo @echo off
echo REM Script temporal para VisiFruit con variables de entorno
echo set TCL_LIBRARY=%PYTHON_DIR%\tcl\tcl8.6
echo set TK_LIBRARY=%PYTHON_DIR%\tcl\tk8.6
echo python visifruit_launcher.py
echo pause
) > start_launcher_fixed.bat

echo ✅ Creado: start_launcher_fixed.bat

REM Opción 4: Verificar archivos Tcl
echo.
echo [4/4] Verificando archivos Tcl...
if exist "%PYTHON_DIR%\tcl\tcl8.6\init.tcl" (
    echo ✅ init.tcl encontrado
) else (
    echo ❌ init.tcl no encontrado en %PYTHON_DIR%\tcl\tcl8.6\
    echo.
    echo DIAGNÓSTICO:
    echo - Python puede estar instalado incorrectamente
    echo - Falta el componente tcl/tk
    echo - Necesitas reinstalar Python
)

echo.
echo ========================================
echo    RESUMEN Y RECOMENDACIONES
echo ========================================
echo.
echo OPCIONES PARA SOLUCIONAR:
echo.
echo 1. 🚀 RÁPIDO: Usa el launcher simple
echo    python visifruit_launcher_simple.py
echo.
echo 2. 🔧 TEMPORAL: Prueba el script con variables
echo    start_launcher_fixed.bat  
echo.
echo 3. 🛠️ DEFINITIVO: Reinstala Python
echo    - Ve a python.org
echo    - Descarga Python 3.11 o 3.12 (más estables)
echo    - Marca "Add Python to PATH" y "tcl/tk and IDLE"
echo.
echo 4. 🪟 MICROSOFT STORE: Instala Python desde Store
echo    - Más simple y sin problemas de configuración
echo.
pause
