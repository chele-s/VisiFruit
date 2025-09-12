# =============================================================================
# Script PowerShell maestro para iniciar el Sistema Completo VisiFruit
# Backend (Puerto 8001) + Frontend (Puerto 3000)
# =============================================================================

param(
    [switch]$SkipPortCheck,
    [switch]$SkipDependencies,
    [switch]$Verbose
)

function Write-Header {
    Write-Host ""
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host "    VISIFRUIT SISTEMA COMPLETO v3.0" -ForegroundColor Cyan
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Step {
    param([string]$Message, [string]$Color = "Green")
    $timestamp = Get-Date -Format 'HH:mm:ss'
    Write-Host "[$timestamp] $Message" -ForegroundColor $Color
}

function Write-Error-Step {
    param([string]$Message)
    $timestamp = Get-Date -Format 'HH:mm:ss'
    Write-Host "[$timestamp] ERROR: $Message" -ForegroundColor Red
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

function Test-Command {
    param([string]$Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

try {
    Write-Header

    # [1/8] Verificar ubicación
    Write-Step "[1/8] Verificando ubicación del proyecto..."
    if (-not (Test-Path "main_etiquetadora.py")) {
        Write-Error-Step "No estás en la raíz del proyecto VisiFruit"
        Write-Host "Ejecuta este script desde la carpeta que contiene main_etiquetadora.py" -ForegroundColor Red
        Read-Host "Presiona Enter para salir"
        exit 1
    }
    Write-Success "Ubicación correcta"

    # [2/8] Configurar variables de entorno
    Write-Step "[2/8] Configurando variables de entorno..."
    $env:PYTHONIOENCODING = "utf-8"
    $env:PYTHONLEGACYWINDOWSSTDIO = "utf-8"
    $env:PYTHONPATH = $PWD.Path
    $env:FRUPRINT_ENV = "development"
    Write-Success "Variables configuradas"

    # [3/8] Verificar Python y entorno virtual
    Write-Step "[3/8] Verificando entorno virtual Python..."
    if (-not (Test-Path "venv\Scripts\python.exe")) {
        Write-Error-Step "Entorno virtual no encontrado"
        Write-Host "Ejecuta: python -m venv venv" -ForegroundColor Yellow
        Read-Host "Presiona Enter para salir"
        exit 1
    }
    Write-Success "Entorno virtual encontrado"

    # [4/8] Verificar Node.js
    Write-Step "[4/8] Verificando Node.js..."
    if (-not (Test-Command "node")) {
        Write-Error-Step "Node.js no está instalado"
        Write-Host "Instala Node.js desde https://nodejs.org/" -ForegroundColor Yellow
        Read-Host "Presiona Enter para salir"
        exit 1
    }
    $nodeVersion = node --version
    Write-Success "Node.js $nodeVersion encontrado"

    # [5/8] Verificar puertos (opcional)
    if (-not $SkipPortCheck) {
        Write-Step "[5/8] Verificando puertos disponibles..."
        try {
            $pythonExe = "venv\Scripts\python.exe"
            & $pythonExe check_ports.py
            if ($LASTEXITCODE -ne 0) {
                Write-Warning "Algunos puertos pueden estar ocupados"
                $continue = Read-Host "¿Continuar de todos modos? (S/N)"
                if ($continue -notmatch "^[SsYy]") {
                    Write-Host "Operación cancelada por el usuario" -ForegroundColor Yellow
                    exit 0
                }
            }
        }
        catch {
            Write-Warning "No se pudo verificar puertos: $_"
        }
    }
    else {
        Write-Step "[5/8] Verificación de puertos omitida"
    }

    # [6/8] Crear directorios necesarios
    Write-Step "[6/8] Preparando directorios..."
    $backendLogsDir = "Interfaz_Usuario\Backend\logs"
    if (-not (Test-Path $backendLogsDir)) {
        New-Item -ItemType Directory -Path $backendLogsDir -Force | Out-Null
        Write-Host "   - Creado directorio logs/" -ForegroundColor Gray
    }
    Write-Success "Directorios preparados"

    # [7/8] Preparar frontend
    Write-Step "[7/8] Preparando frontend React..."
    Push-Location "Interfaz_Usuario\VisiFruit"
    
    try {
        # Verificar package.json
        if (-not (Test-Path "package.json")) {
            Write-Error-Step "No se encontró package.json en el frontend"
            exit 1
        }

        # Instalar dependencias si no existen
        if (-not (Test-Path "node_modules") -and -not $SkipDependencies) {
            Write-Host "   Instalando dependencias npm..." -ForegroundColor Gray
            npm install --silent
            if ($LASTEXITCODE -ne 0) {
                Write-Error-Step "Fallo instalación npm"
                exit 1
            }
            Write-Success "Dependencias instaladas"
        }

        # Crear .env si no existe
        if (-not (Test-Path ".env")) {
            Write-Host "   Creando configuración frontend..." -ForegroundColor Gray
            @"
# Configuración del Frontend VisiFruit
VITE_API_URL=http://localhost:8001
VITE_WS_URL=ws://localhost:8001/ws
VITE_DEV_PORT=3000
VITE_ENVIRONMENT=development
VITE_ENABLE_3D=true
VITE_ENABLE_ANIMATIONS=true
VITE_ENABLE_WEBSOCKETS=true
"@ | Out-File -FilePath ".env" -Encoding utf8
            Write-Success "Configuración frontend creada"
        }
    }
    finally {
        Pop-Location
    }

    # [8/8] Iniciar servicios
    Write-Step "[8/8] Iniciando servicios..."
    Write-Host ""
    Write-Host "================================================" -ForegroundColor Green
    Write-Host "    SISTEMA INICIADO EXITOSAMENTE" -ForegroundColor Green
    Write-Host "================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "🟢 Backend API:     " -NoNewline; Write-Host "http://localhost:8001" -ForegroundColor Cyan
    Write-Host "🟢 Dashboard API:   " -NoNewline; Write-Host "http://localhost:8001/api/docs" -ForegroundColor Cyan
    Write-Host "🟢 Frontend React:  " -NoNewline; Write-Host "http://localhost:3000" -ForegroundColor Cyan
    Write-Host "🟢 WebSocket:       " -NoNewline; Write-Host "ws://localhost:8001/ws" -ForegroundColor Cyan
    Write-Host ""
    Write-Warning "IMPORTANTE:"
    Write-Host "   - Backend se iniciará en ventana 1" -ForegroundColor Yellow
    Write-Host "   - Frontend se iniciará en ventana 2" -ForegroundColor Yellow
    Write-Host "   - Usa Ctrl+C para detener cada servicio" -ForegroundColor Yellow
    Write-Host "================================================" -ForegroundColor Green
    Write-Host ""

    # Iniciar backend
    Write-Step "Iniciando backend..."
    $backendCommand = "venv\Scripts\python.exe Interfaz_Usuario\Backend\main.py"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "& { Set-Location '$PWD'; $backendCommand }" -WindowStyle Normal

    # Esperar para que el backend inicie
    Write-Step "Esperando que el backend inicie..."
    Start-Sleep -Seconds 5

    # Iniciar frontend
    Write-Step "Iniciando frontend..."
    $frontendPath = Join-Path $PWD "Interfaz_Usuario\VisiFruit"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "& { Set-Location '$frontendPath'; npm run dev }" -WindowStyle Normal

    Write-Host ""
    Write-Host "================================================" -ForegroundColor Green
    Write-Host "Sistema completo iniciado exitosamente!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Para detener:" -ForegroundColor Yellow
    Write-Host "  - Usa Ctrl+C en la ventana del Backend" -ForegroundColor Yellow
    Write-Host "  - Usa Ctrl+C en la ventana del Frontend" -ForegroundColor Yellow
    Write-Host "  - O cierra las ventanas directamente" -ForegroundColor Yellow
    Write-Host "================================================" -ForegroundColor Green
    Write-Host ""

    Read-Host "Presiona Enter para cerrar esta ventana (los servicios seguirán ejecutándose)"

}
catch {
    Write-Error-Step "Error inesperado: $_"
    Write-Host $_.ScriptStackTrace -ForegroundColor Red
    Read-Host "Presiona Enter para salir"
    exit 1
}
