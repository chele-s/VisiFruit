# =============================================================================
# Script PowerShell para iniciar el backend de VisiFruit con verificaciones completas
# =============================================================================

param(
    [switch]$SkipPortCheck,
    [switch]$Verbose
)

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    VISIFRUIT BACKEND STARTER PS v2.0" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Función para logging con colores
function Write-Step {
    param([string]$Message, [string]$Color = "Green")
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] $Message" -ForegroundColor $Color
}

function Write-Error-Step {
    param([string]$Message)
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ERROR: $Message" -ForegroundColor Red
}

function Write-Warning-Step {
    param([string]$Message)
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] WARNING: $Message" -ForegroundColor Yellow
}

try {
    # [1/8] Verificar ubicación
    Write-Step "[1/8] Verificando ubicación del proyecto..."
    if (-not (Test-Path "main_etiquetadora.py")) {
        Write-Error-Step "No estás en la raíz del proyecto VisiFruit"
        Write-Host "Ejecuta este script desde la carpeta que contiene main_etiquetadora.py" -ForegroundColor Red
        Read-Host "Presiona Enter para salir"
        exit 1
    }

    # [2/8] Configurar variables de entorno
    Write-Step "[2/8] Configurando variables de entorno..."
    $env:PYTHONIOENCODING = "utf-8"
    $env:PYTHONLEGACYWINDOWSSTDIO = "utf-8"
    $env:PYTHONPATH = $PWD.Path
    $env:FRUPRINT_ENV = "development"

    # [3/8] Verificar entorno virtual
    Write-Step "[3/8] Verificando entorno virtual..."
    if (-not (Test-Path "venv\Scripts\python.exe")) {
        Write-Error-Step "Entorno virtual no encontrado"
        Write-Host "Ejecuta: python -m venv venv" -ForegroundColor Yellow
        Read-Host "Presiona Enter para salir"
        exit 1
    }

    # [4/8] Activar entorno virtual y verificar dependencias
    Write-Step "[4/8] Activando entorno virtual y verificando dependencias..."
    $pythonExe = "venv\Scripts\python.exe"
    
    try {
        & $pythonExe -c "import uvicorn, fastapi" 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Error-Step "Dependencias no instaladas"
            Write-Host "Ejecuta: .\venv\Scripts\pip.exe install -r requirements.txt" -ForegroundColor Yellow
            Read-Host "Presiona Enter para salir"
            exit 1
        }
    } catch {
        Write-Error-Step "Error verificando dependencias: $_"
        exit 1
    }

    # [5/8] Verificar puertos (opcional)
    if (-not $SkipPortCheck) {
        Write-Step "[5/8] Verificando puertos disponibles..."
        try {
            & $pythonExe check_ports.py
            if ($LASTEXITCODE -ne 0) {
                Write-Warning-Step "Algunos puertos pueden estar ocupados"
                $continue = Read-Host "¿Continuar de todos modos? (S/N)"
                if ($continue -notmatch "^[SsYy]") {
                    Write-Host "Operación cancelada por el usuario" -ForegroundColor Yellow
                    exit 0
                }
            }
        } catch {
            Write-Warning-Step "No se pudo verificar puertos: $_"
        }
    } else {
        Write-Step "[5/8] Verificación de puertos omitida"
    }

    # [6/8] Crear directorios
    Write-Step "[6/8] Preparando directorios..."
    $backendLogsDir = "Interfaz_Usuario\Backend\logs"
    if (-not (Test-Path $backendLogsDir)) {
        New-Item -ItemType Directory -Path $backendLogsDir -Force | Out-Null
        Write-Host "   - Creado directorio logs/" -ForegroundColor Gray
    }

    # [7/8] Verificar archivos del backend
    Write-Step "[7/8] Verificando archivos del backend..."
    $backendMainPath = "Interfaz_Usuario\Backend\main.py"
    if (-not (Test-Path $backendMainPath)) {
        Write-Error-Step "No se encontró el archivo main.py del backend"
        exit 1
    }

    # [8/8] Iniciar backend
    Write-Step "[8/8] Iniciando servidor backend..."
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "    BACKEND INICIADO EXITOSAMENTE" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Backend disponible en: " -NoNewline; Write-Host "http://localhost:8001" -ForegroundColor Cyan
    Write-Host "Dashboard API: " -NoNewline; Write-Host "http://localhost:8001/api/docs" -ForegroundColor Cyan
    Write-Host "WebSocket realtime: " -NoNewline; Write-Host "ws://localhost:8001/ws/realtime" -ForegroundColor Cyan
    Write-Host "WebSocket dashboard: " -NoNewline; Write-Host "ws://localhost:8001/ws/dashboard" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Presiona Ctrl+C para detener el servidor" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""

    # Cambiar al directorio del backend y ejecutar
    Push-Location "Interfaz_Usuario\Backend"
    try {
        & $pythonExe main.py
    } finally {
        Pop-Location
    }

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Backend detenido correctamente." -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green

} catch {
    Write-Error-Step "Error inesperado: $_"
    Write-Host $_.ScriptStackTrace -ForegroundColor Red
    Read-Host "Presiona Enter para salir"
    exit 1
}

Read-Host "Presiona Enter para salir"
