@echo off
REM ========================================
REM   VisiFruit AI Inference Server
REM   Servidor optimizado para GPU/CPU
REM ========================================

title VisiFruit AI Server

echo.
echo ========================================
echo   VisiFruit AI Inference Server
echo ========================================
echo.

REM Verificar que estamos en el directorio correcto
if not exist "ai_inference_server.py" (
    echo ERROR: No se encuentra ai_inference_server.py
    echo Asegurate de ejecutar este script desde el directorio VisiFruit
    pause
    exit /b 1
)

REM Activar entorno virtual si existe
if exist "venv\Scripts\activate.bat" (
    echo [+] Activando entorno virtual...
    call venv\Scripts\activate.bat
) else (
    echo [!] No se encontro entorno virtual. Usando Python del sistema...
)

REM Verificar que Python esta instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no esta instalado o no esta en PATH
    pause
    exit /b 1
)

REM Configurar variables de entorno
echo [+] Configurando variables de entorno...
set MODEL_PATH=weights/best.pt
set MODEL_DEVICE=cuda
set MODEL_FP16=true
set AUTH_ENABLED=true
set AUTH_TOKENS=visifruittoken2025,debugtoken
set SERVER_HOST=0.0.0.0
set SERVER_PORT=9000
set RATE_LIMIT=60/minute
set MAX_IMAGE_SIZE=1920
set ENABLE_CACHE=true

REM Verificar que el modelo existe
if not exist "%MODEL_PATH%" (
    echo.
    echo [!] ADVERTENCIA: No se encuentra el modelo en %MODEL_PATH%
    echo     El servidor se iniciara pero fallara al recibir peticiones.
    echo.
    timeout /t 3 >nul
)

REM Mostrar configuracion
echo.
echo ========================================
echo   CONFIGURACION
echo ========================================
echo   Modelo:        %MODEL_PATH%
echo   Device:        %MODEL_DEVICE%
echo   FP16:          %MODEL_FP16%
echo   Host:          %SERVER_HOST%
echo   Puerto:        %SERVER_PORT%
echo   Auth:          %AUTH_ENABLED%
echo ========================================
echo.

REM Preguntar si desea ver GPU info (si esta disponible)
where nvidia-smi >nul 2>&1
if not errorlevel 1 (
    echo [+] GPU NVIDIA detectada. Mostrando informacion:
    nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv
    echo.
)

echo [+] Iniciando servidor...
echo     Presiona Ctrl+C para detener
echo.

REM Iniciar servidor con uvicorn
python ai_inference_server.py

REM Si el servidor se detiene
echo.
echo ========================================
echo   Servidor detenido
echo ========================================
pause
