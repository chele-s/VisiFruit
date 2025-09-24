#!/bin/bash

# 🚀 VisiFruit Complete System Startup Script
# Inicia todos los servicios necesarios para el sistema completo
#
# Servicios:
# - Sistema Principal (main_etiquetadora.py) - Puerto 8000
# - Demo Web Server (demo_sistema_web_server.py) - Puerto 8002
# - Backend Dashboard - Puerto 8001
# - Frontend React - Puerto 3000

set -e  # Salir si cualquier comando falla

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Función para logging
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_header() {
    echo -e "${PURPLE}$1${NC}"
}

# Función para verificar si un puerto está en uso
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Puerto en uso
    else
        return 1  # Puerto libre
    fi
}

# Función para matar procesos en un puerto específico
kill_port() {
    local port=$1
    local pids=$(lsof -Pi :$port -sTCP:LISTEN -t 2>/dev/null)
    
    if [ -n "$pids" ]; then
        log_warning "Matando procesos en puerto $port: $pids"
        echo $pids | xargs kill -15 2>/dev/null || true
        sleep 2
        
        # Verificar si todavía hay procesos
        local remaining_pids=$(lsof -Pi :$port -sTCP:LISTEN -t 2>/dev/null)
        if [ -n "$remaining_pids" ]; then
            log_warning "Forzando cierre de procesos restantes en puerto $port"
            echo $remaining_pids | xargs kill -9 2>/dev/null || true
        fi
    fi
}

# Verificar dependencias
check_dependencies() {
    log_header "🔍 Verificando dependencias..."
    
    # Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 no encontrado"
        exit 1
    fi
    
    # Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js no encontrado"
        exit 1
    fi
    
    # npm
    if ! command -v npm &> /dev/null; then
        log_error "npm no encontrado"
        exit 1
    fi
    
    log_success "Todas las dependencias están disponibles"
}

# Limpiar puertos ocupados
cleanup_ports() {
    log_header "🧹 Limpiando puertos ocupados..."
    
    local ports=(8000 8001 8002 3000)
    
    for port in "${ports[@]}"; do
        if check_port $port; then
            log_warning "Puerto $port está ocupado, liberando..."
            kill_port $port
        fi
    done
    
    sleep 2
    log_success "Puertos limpiados"
}

# Crear archivos de log
setup_logging() {
    log_header "📝 Configurando logging..."
    
    local log_dir="logs/services"
    mkdir -p "$log_dir"
    
    # Crear archivos de log con timestamp
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    
    export MAIN_LOG="$log_dir/main_system_$timestamp.log"
    export DEMO_LOG="$log_dir/demo_server_$timestamp.log"  
    export BACKEND_LOG="$log_dir/backend_$timestamp.log"
    export FRONTEND_LOG="$log_dir/frontend_$timestamp.log"
    
    log_success "Archivos de log creados en $log_dir"
}

# Instalar dependencias Python si es necesario
install_python_deps() {
    log_header "🐍 Verificando dependencias Python..."
    
    # Verificar FastAPI y uvicorn para el demo web server
    if ! python3 -c "import fastapi, uvicorn" 2>/dev/null; then
        log_info "Instalando FastAPI y uvicorn..."
        pip3 install fastapi uvicorn
    fi
    
    log_success "Dependencias Python verificadas"
}

# Instalar dependencias Node.js si es necesario
install_node_deps() {
    log_header "📦 Verificando dependencias Node.js..."
    
    local frontend_dir="Interfaz_Usuario/VisiFruit"
    
    if [ ! -d "$frontend_dir/node_modules" ]; then
        log_info "Instalando dependencias del frontend..."
        cd "$frontend_dir"
        npm install
        cd - > /dev/null
    fi
    
    log_success "Dependencias Node.js verificadas"
}

# Iniciar sistema principal
start_main_system() {
    log_header "🏷️ Iniciando Sistema Principal (puerto 8000)..."
    
    if [ ! -f "main_etiquetadora.py" ]; then
        log_error "main_etiquetadora.py no encontrado"
        return 1
    fi
    
    # Configurar variables de entorno
    export AUTO_START_FRONTEND=false  # Lo iniciaremos manualmente
    export AUTO_START_BACKEND=false   # Lo iniciaremos manualmente
    
    log_info "Iniciando main_etiquetadora.py..."
    python3 main_etiquetadora.py > "$MAIN_LOG" 2>&1 &
    local main_pid=$!
    
    echo $main_pid > .main_system.pid
    
    # Esperar a que el servicio esté listo
    log_info "Esperando que el sistema principal esté listo..."
    local retries=0
    while [ $retries -lt 30 ]; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            log_success "Sistema Principal listo en puerto 8000 (PID: $main_pid)"
            return 0
        fi
        sleep 2
        ((retries++))
    done
    
    log_error "Sistema Principal no respondió en el tiempo esperado"
    return 1
}

# Iniciar demo web server
start_demo_server() {
    log_header "🔧 Iniciando Demo Web Server (puerto 8002)..."
    
    if [ ! -f "Control_Etiquetado/demo_sistema_web_server.py" ]; then
        log_error "demo_sistema_web_server.py no encontrado"
        return 1
    fi
    
    log_info "Iniciando demo web server..."
    python3 Control_Etiquetado/demo_sistema_web_server.py > "$DEMO_LOG" 2>&1 &
    local demo_pid=$!
    
    echo $demo_pid > .demo_server.pid
    
    # Esperar a que el servicio esté listo
    log_info "Esperando que el demo web server esté listo..."
    local retries=0
    while [ $retries -lt 15 ]; do
        if curl -s http://localhost:8002/health > /dev/null 2>&1; then
            log_success "Demo Web Server listo en puerto 8002 (PID: $demo_pid)"
            return 0
        fi
        sleep 2
        ((retries++))
    done
    
    log_error "Demo Web Server no respondió en el tiempo esperado"
    return 1
}

# Iniciar backend dashboard
start_backend() {
    log_header "📊 Iniciando Backend Dashboard (puerto 8001)..."
    
    local backend_dir="Interfaz_Usuario/Backend"
    
    if [ ! -d "$backend_dir" ]; then
        log_error "Backend directory no encontrado"
        return 1
    fi
    
    if [ ! -f "$backend_dir/main.py" ]; then
        log_error "Backend main.py no encontrado"
        return 1
    fi
    
    log_info "Iniciando backend dashboard..."
    cd "$backend_dir"
    python3 -u main.py > "../../$BACKEND_LOG" 2>&1 &
    local backend_pid=$!
    cd - > /dev/null
    
    echo $backend_pid > .backend.pid
    
    # Esperar a que el servicio esté listo
    log_info "Esperando que el backend esté listo..."
    local retries=0
    while [ $retries -lt 15 ]; do
        if curl -s http://localhost:8001/health > /dev/null 2>&1; then
            log_success "Backend Dashboard listo en puerto 8001 (PID: $backend_pid)"
            return 0
        fi
        sleep 2
        ((retries++))
    done
    
    log_error "Backend Dashboard no respondió en el tiempo esperado"
    return 1
}

# Iniciar frontend
start_frontend() {
    log_header "🎨 Iniciando Frontend React (puerto 3000)..."
    
    local frontend_dir="Interfaz_Usuario/VisiFruit"
    
    if [ ! -d "$frontend_dir" ]; then
        log_error "Frontend directory no encontrado"
        return 1
    fi
    
    # Configurar variables de entorno para el frontend
    export VITE_API_URL="http://localhost:8001"
    export VITE_WS_URL="ws://localhost:8001/ws/realtime"
    export VITE_MAIN_API_URL="http://localhost:8000"
    export VITE_DEMO_API_URL="http://localhost:8002"
    
    log_info "Iniciando frontend..."
    cd "$frontend_dir"
    npm run dev -- --host 0.0.0.0 --port 3000 > "../../$FRONTEND_LOG" 2>&1 &
    local frontend_pid=$!
    cd - > /dev/null
    
    echo $frontend_pid > .frontend.pid
    
    # Esperar a que el servicio esté listo
    log_info "Esperando que el frontend esté listo..."
    local retries=0
    while [ $retries -lt 30 ]; do
        if curl -s http://localhost:3000 > /dev/null 2>&1; then
            log_success "Frontend React listo en puerto 3000 (PID: $frontend_pid)"
            return 0
        fi
        sleep 3
        ((retries++))
    done
    
    log_error "Frontend no respondió en el tiempo esperado"
    return 1
}

# Mostrar estado de servicios
show_status() {
    log_header "📊 Estado de Servicios:"
    echo ""
    
    # Función para verificar estado de servicio
    check_service() {
        local name=$1
        local port=$2
        local url="http://localhost:$port/health"
        
        if curl -s "$url" > /dev/null 2>&1; then
            log_success "$name: ✅ Funcionando (puerto $port)"
            echo "   🌐 URL: http://localhost:$port"
        else
            log_error "$name: ❌ No disponible (puerto $port)"
        fi
    }
    
    check_service "Sistema Principal" "8000"
    check_service "Demo Web Server" "8002" 
    check_service "Backend Dashboard" "8001"
    
    # Frontend (no tiene /health)
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        log_success "Frontend React: ✅ Funcionando (puerto 3000)"
        echo "   🌐 URL: http://localhost:3000"
    else
        log_error "Frontend React: ❌ No disponible (puerto 3000)"
    fi
    
    echo ""
    log_header "📖 URLs Importantes:"
    echo "   🎨 Frontend Principal: http://localhost:3000"
    echo "   🎛️ Control de Banda: http://localhost:3000 (Control de Banda en sidebar)"
    echo "   📊 Dashboard API: http://localhost:8001/docs"
    echo "   🏷️ Sistema Principal API: http://localhost:8000/docs"
    echo "   🔧 Demo Server API: http://localhost:8002/docs"
    echo ""
}

# Función de limpieza al salir
cleanup() {
    log_header "🛑 Deteniendo servicios..."
    
    # Leer PIDs y matar procesos
    if [ -f .main_system.pid ]; then
        local pid=$(cat .main_system.pid)
        kill $pid 2>/dev/null && log_info "Sistema Principal detenido (PID: $pid)"
        rm -f .main_system.pid
    fi
    
    if [ -f .demo_server.pid ]; then
        local pid=$(cat .demo_server.pid)
        kill $pid 2>/dev/null && log_info "Demo Web Server detenido (PID: $pid)"
        rm -f .demo_server.pid
    fi
    
    if [ -f .backend.pid ]; then
        local pid=$(cat .backend.pid)
        kill $pid 2>/dev/null && log_info "Backend detenido (PID: $pid)"
        rm -f .backend.pid
    fi
    
    if [ -f .frontend.pid ]; then
        local pid=$(cat .frontend.pid)
        kill $pid 2>/dev/null && log_info "Frontend detenido (PID: $pid)"
        rm -f .frontend.pid
    fi
    
    # Cleanup adicional de puertos
    cleanup_ports
    
    log_success "Limpieza completada"
    exit 0
}

# Configurar trap para cleanup
trap cleanup SIGINT SIGTERM

# Función principal
main() {
    log_header "🚀 VisiFruit Complete System Startup"
    log_header "===================================="
    echo ""
    
    # Verificaciones iniciales
    check_dependencies
    setup_logging
    
    # Limpiar estado anterior
    cleanup_ports
    
    # Instalar dependencias
    install_python_deps
    install_node_deps
    
    # Variables para rastrear servicios iniciados
    local services_started=0
    local total_services=4
    
    # Iniciar servicios en orden
    echo ""
    log_header "🔄 Iniciando servicios..."
    
    # 1. Sistema Principal
    if start_main_system; then
        ((services_started++))
    fi
    
    # 2. Demo Web Server
    if start_demo_server; then
        ((services_started++))
    fi
    
    # 3. Backend Dashboard
    if start_backend; then
        ((services_started++))
    fi
    
    # 4. Frontend
    if start_frontend; then
        ((services_started++))
    fi
    
    echo ""
    
    # Mostrar resultado
    if [ $services_started -eq $total_services ]; then
        log_success "Todos los servicios iniciados correctamente ($services_started/$total_services)"
    elif [ $services_started -gt 0 ]; then
        log_warning "Algunos servicios iniciados ($services_started/$total_services)"
        log_warning "Revisa los logs para más detalles"
    else
        log_error "No se pudo iniciar ningún servicio"
        cleanup
        exit 1
    fi
    
    # Mostrar estado y URLs
    echo ""
    show_status
    
    # Instrucciones finales
    log_header "🎯 Sistema VisiFruit iniciado"
    echo ""
    log_info "Para usar el Control de Banda:"
    log_info "1. Abre http://localhost:3000"
    log_info "2. Haz clic en 'Control de Banda' en la barra lateral"
    log_info "3. El sistema detectará automáticamente las conexiones"
    echo ""
    log_info "Presiona Ctrl+C para detener todos los servicios"
    
    # Mostrar logs en tiempo real (opcional)
    if [ "$1" = "--tail-logs" ]; then
        log_info "Mostrando logs en tiempo real..."
        tail -f logs/services/*.log
    else
        log_info "Para ver logs: tail -f logs/services/*.log"
    fi
    
    # Mantener script ejecutándose
    while true; do
        sleep 5
        
        # Verificar que los servicios sigan funcionando
        local running_services=0
        
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            ((running_services++))
        fi
        if curl -s http://localhost:8002/health > /dev/null 2>&1; then
            ((running_services++))
        fi
        if curl -s http://localhost:8001/health > /dev/null 2>&1; then
            ((running_services++))
        fi
        if curl -s http://localhost:3000 > /dev/null 2>&1; then
            ((running_services++))
        fi
        
        if [ $running_services -eq 0 ]; then
            log_error "Todos los servicios se han detenido"
            break
        fi
    done
}

# Verificar si se ejecuta directamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi

