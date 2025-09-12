# Script de prueba para verificar endpoints del backend VisiFruit
# Autor: Gabriel Calderón
# Fecha: 2025-08-12

param(
    [string]$BaseUrl = "http://localhost:8001",
    [int]$Timeout = 10
)

Write-Host "🧪 Iniciando pruebas del backend VisiFruit..." -ForegroundColor Cyan
Write-Host "📍 URL Base: $BaseUrl" -ForegroundColor Yellow
Write-Host "⏱️  Timeout: ${Timeout}s" -ForegroundColor Yellow
Write-Host ""

# Función para hacer requests HTTP
function Test-Endpoint {
    param(
        [string]$Method,
        [string]$Endpoint,
        [string]$Description,
        [object]$Body = $null
    )
    
    $url = "$BaseUrl$Endpoint"
    $headers = @{
        "Content-Type" = "application/json"
    }
    
    try {
        $params = @{
            Uri = $url
            Method = $Method
            Headers = $headers
            TimeoutSec = $Timeout
        }
        
        if ($Body) {
            $params.Body = $Body | ConvertTo-Json -Depth 10
        }
        
        $response = Invoke-RestMethod @params -ErrorAction Stop
        
        Write-Host " ✅ $Description" -ForegroundColor Green
        Write-Host "   📍 $Method $Endpoint" -ForegroundColor Gray
        Write-Host "   📊 Status: $($response.StatusCode)" -ForegroundColor Gray
        
        if ($response -and $response.GetType().Name -ne "String") {
            $responseKeys = $response.PSObject.Properties.Name
            Write-Host "   📋 Respuesta: $($responseKeys -join ', ')" -ForegroundColor Gray
        }
        
        return $true
        
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host " ❌ $Description" -ForegroundColor Red
        Write-Host "   📍 $Method $Endpoint" -ForegroundColor Gray
        Write-Host "   ⚠️  Código: $statusCode" -ForegroundColor Yellow
        Write-Host "   💬 Error: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Función para probar WebSocket (simulación)
function Test-WebSocket {
    param(
        [string]$Endpoint,
        [string]$Description
    )
    
    Write-Host " 🔌 $Description" -ForegroundColor Blue
    Write-Host "   📍 WebSocket: $Endpoint" -ForegroundColor Gray
    Write-Host "   ℹ️  WebSocket requiere cliente especial - verificar manualmente" -ForegroundColor Yellow
}

# Contador de resultados
$totalTests = 0
$passedTests = 0
$failedTests = 0

# 1. Endpoints básicos del sistema
Write-Host "🚀 === ENDPOINTS BÁSICOS ===" -ForegroundColor Magenta
$totalTests++

if (Test-Endpoint -Method "GET" -Endpoint "/" -Description "Endpoint raíz del sistema") {
    $passedTests++
} else {
    $failedTests++
}

$totalTests++
if (Test-Endpoint -Method "GET" -Endpoint "/health" -Description "Check de salud del sistema") {
    $passedTests++
} else {
    $failedTests++
}

$totalTests++
if (Test-Endpoint -Method "GET" -Endpoint "/api/status/ultra" -Description "Estado ultra-detallado del sistema") {
    $passedTests++
} else {
    $failedTests++
}

# 2. Endpoints de métricas
Write-Host "📊 === ENDPOINTS DE MÉTRICAS ===" -ForegroundColor Magenta

$totalTests++
if (Test-Endpoint -Method "GET" -Endpoint "/api/metrics/summary?period=24h" -Description "Resumen de métricas (24h)") {
    $passedTests++
} else {
    $failedTests++
}

$totalTests++
if (Test-Endpoint -Method "GET" -Endpoint "/api/metrics/performance" -Description "Métricas de rendimiento") {
    $passedTests++
} else {
    $failedTests++
}

$totalTests++
if (Test-Endpoint -Method "GET" -Endpoint "/api/metrics/history/production?period=24h" -Description "Historial de producción (24h)") {
    $passedTests++
} else {
    $failedTests++
}

# 3. Endpoints de producción
Write-Host "🏭 === ENDPOINTS DE PRODUCCIÓN ===" -ForegroundColor Magenta

$totalTests++
if (Test-Endpoint -Method "GET" -Endpoint "/api/production/status" -Description "Estado de producción") {
    $passedTests++
} else {
    $failedTests++
}

$totalTests++
if (Test-Endpoint -Method "GET" -Endpoint "/api/production/metrics/realtime" -Description "Métricas en tiempo real") {
    $passedTests++
} else {
    $failedTests++
}

# 4. Endpoints de alertas
Write-Host "🚨 === ENDPOINTS DE ALERTAS ===" -ForegroundColor Magenta

$totalTests++
if (Test-Endpoint -Method "GET" -Endpoint "/api/alerts/" -Description "Lista de alertas") {
    $passedTests++
} else {
    $failedTests++
}

# 5. Endpoints del sistema
Write-Host "⚙️ === ENDPOINTS DEL SISTEMA ===" -ForegroundColor Magenta

$totalTests++
if (Test-Endpoint -Method "GET" -Endpoint "/api/system/performance" -Description "Rendimiento del sistema") {
    $passedTests++
} else {
    $failedTests++
}

$totalTests++
if (Test-Endpoint -Method "GET" -Endpoint "/api/system/status" -Description "Estado del sistema") {
    $passedTests++
} else {
    $failedTests++
}

# 6. Endpoints de configuración
Write-Host "🔧 === ENDPOINTS DE CONFIGURACIÓN ===" -ForegroundColor Magenta

$totalTests++
if (Test-Endpoint -Method "GET" -Endpoint "/api/config/current" -Description "Configuración actual") {
    $passedTests++
} else {
    $failedTests++
}

# 7. WebSockets
Write-Host "🔌 === WEBSOCKETS ===" -ForegroundColor Magenta

Test-WebSocket -Endpoint "/ws/realtime" -Description "WebSocket tiempo real"
Test-WebSocket -Endpoint "/ws/dashboard" -Description "WebSocket dashboard"
Test-WebSocket -Endpoint "/ws/alerts" -Description "WebSocket alertas"

# 8. Simulación de producción
Write-Host "🎮 === SIMULACIÓN ===" -ForegroundColor Magenta

$totalTests++
if (Test-Endpoint -Method "POST" -Endpoint "/api/system/simulate" -Description "Simular datos de producción") {
    $passedTests++
} else {
    $failedTests++
}

# Resumen de resultados
Write-Host ""
Write-Host "📋 === RESUMEN DE PRUEBAS ===" -ForegroundColor Cyan
Write-Host "✅ Pruebas exitosas: $passedTests" -ForegroundColor Green
Write-Host "❌ Pruebas fallidas: $failedTests" -ForegroundColor Red
Write-Host "📊 Total de pruebas: $totalTests" -ForegroundColor Blue

if ($failedTests -eq 0) {
    Write-Host "🎉 ¡Todas las pruebas pasaron exitosamente!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Algunas pruebas fallaron. Revisar logs del backend." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🔍 Para más detalles, revisar:" -ForegroundColor Gray
Write-Host "   📁 Logs: logs/backend_ultra.log" -ForegroundColor Gray
Write-Host "   🌐 API Docs: $BaseUrl/api/docs" -ForegroundColor Gray
Write-Host "   📊 Dashboard: $BaseUrl/api/redoc" -ForegroundColor Gray
