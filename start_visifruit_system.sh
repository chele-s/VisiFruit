#!/bin/bash
# ============================================================================
# 🚀 VisiFruit Sistema Completo - Script de Inicio Automático
# ============================================================================
# Script para iniciar el sistema completo VisiFruit en Raspberry Pi 5
# Incluye backend, frontend y sistema principal de etiquetado
# 
# Autor: Gabriel Calderón, Elias Bautista, Cristian Hernandez
# Fecha: Julio 2025
# Versión: 3.0.0-ULTRA
# ============================================================================

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Configuración
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
VENV_PATH="$PROJECT_ROOT/venv"
PYTHON_EXEC="$VENV_PATH/bin/python"
LOG_DIR="$PROJECT_ROOT/logs"
PIDFILE_DIR="$PROJECT_ROOT/.pids"

# Crear directorios necesarios
mkdir -p "$LOG_DIR" "$PIDFILE_DIR"

# Función para imprimir headers
print_header() {
    echo -e "${CYAN}"
    echo "=============================================="
    echo "    🚀 VisiFruit Sistema Ultra v3.0"
    echo "=============================================="
    echo -e "${NC}"
}

# Función para imprimir mensajes con timestamp
log_message() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        "INFO")
            echo -e "${GREEN}[INFO]${NC} [$timestamp] $message"
            ;;
        "WARN")
            echo -e "${YELLOW}[WARN]${NC} [$timestamp] $message"
            ;;
        "ERROR")
            echo -e "${RED}[ERROR]${NC} [$timestamp] $message"
            ;;
        "DEBUG")
            echo -e "${BLUE}[DEBUG]${NC} [$timestamp] $message"
            ;;
        *)
            echo -e "${WHITE}[LOG]${NC} [$timestamp] $message"
            ;;
    esac
}

# Función para verificar si un proceso está corriendo
is_process_running() {
    local pidfile=$1
    if [[ -f "$pidfile" ]]; then
        local pid=$(cat "$pidfile")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        else
            rm -f "$pidfile"
            return 1
        fi
    fi
    return 1
}

# Función para crear archivo .env si no existe
create_env_file() {
    if [[ ! -f "$PROJECT_ROOT/.env" ]]; then
        log_message "WARN" "Archivo .env no encontrado. Creando desde template..."
        if [[ -f "$PROJECT_ROOT/env_config_template.txt" ]]; then
            cp "$PROJECT_ROOT/env_config_template.txt" "$PROJECT_ROOT/.env"
            log_message "INFO" "Archivo .env creado desde template"
        else
            log_message "ERROR" "Template de configuración no encontrado"
            return 1
        fi
    else
        log_message "INFO" "Archivo .env encontrado"
    fi
    return 0
}

# Función para verificar dependencias
check_dependencies() {
    log_message "INFO" "Verificando dependencias del sistema..."
    
    # Verificar Python
    if [[ ! -f "$PYTHON_EXEC" ]]; then
        log_message "ERROR" "Python no encontrado en $PYTHON_EXEC"
        log_message "INFO" "Ejecuta: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
        return 1
    fi
    
    # Verificar Node.js y npm
    if ! command -v npm &> /dev/null; then
        log_message "WARN" "npm no encontrado - frontend no se podrá iniciar"
        log_message "INFO" "Para instalar Node.js: curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt-get install -y nodejs"
    fi
    
    # Verificar dependencias de Python
    log_message "INFO" "Verificando dependencias de Python..."
    "$PYTHON_EXEC" -c "import fastapi, uvicorn" 2>/dev/null
    if [[ $? -ne 0 ]]; then
        log_message "ERROR" "Dependencias de Python faltantes"
        log_message "INFO" "Ejecuta: source venv/bin/activate && pip install -r requirements.txt"
        return 1
    fi
    
    log_message "INFO" "Dependencias verificadas correctamente"
    return 0
}

# Función para verificar hardware GPIO
check_gpio_hardware() {
    log_message "INFO" "Verificando hardware GPIO..."
    
    # Verificar si estamos en Raspberry Pi
    if [[ -f /proc/device-tree/model ]]; then
        local model=$(cat /proc/device-tree/model)
        log_message "INFO" "Modelo detectado: $model"
        
        if [[ $model == *"Raspberry Pi"* ]]; then
            log_message "INFO" "Raspberry Pi detectado - Hardware GPIO disponible"
            
            # Verificar lgpio
            if "$PYTHON_EXEC" -c "import lgpio" 2>/dev/null; then
                log_message "INFO" "lgpio disponible (Raspberry Pi 5 compatible)"
            else
                log_message "WARN" "lgpio no disponible - modo simulación"
            fi
        else
            log_message "WARN" "No es Raspberry Pi - usando modo simulación"
        fi
    else
        log_message "WARN" "Sistema no identificado - usando modo simulación"
    fi
}

# Función para verificar puertos
check_ports() {
    local ports=(3000 8000 8001)
    
    log_message "INFO" "Verificando puertos disponibles..."
    
    for port in "${ports[@]}"; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            log_message "WARN" "Puerto $port ya está en uso"
            
            # Preguntar si queremos matar el proceso
            if [[ "$1" == "--force" ]]; then
                log_message "INFO" "Modo fuerza activado - matando proceso en puerto $port"
                lsof -ti:$port | xargs kill -9 2>/dev/null || true
                sleep 2
            else
                log_message "INFO" "Usa --force para matar procesos automáticamente"
            fi
        else
            log_message "INFO" "Puerto $port disponible"
        fi
    done
}

# Función para iniciar el sistema principal
start_main_system() {
    local pidfile="$PIDFILE_DIR/main_system.pid"
    
    if is_process_running "$pidfile"; then
        log_message "WARN" "Sistema principal ya está corriendo (PID: $(cat $pidfile))"
        return 0
    fi
    
    log_message "INFO" "Iniciando sistema principal de etiquetado..."
    
    cd "$PROJECT_ROOT"
    nohup "$PYTHON_EXEC" -u main_etiquetadora.py > "$LOG_DIR/main_system.log" 2>&1 &
    local pid=$!
    echo $pid > "$pidfile"
    
    # Esperar un poco y verificar que el proceso siga corriendo
    sleep 3
    if kill -0 "$pid" 2>/dev/null; then
        log_message "INFO" "Sistema principal iniciado correctamente (PID: $pid)"
        log_message "INFO" "API principal disponible en: http://localhost:8000"
        return 0
    else
        log_message "ERROR" "Error iniciando sistema principal"
        rm -f "$pidfile"
        return 1
    fi
}

# Función para detener procesos
stop_process() {
    local name=$1
    local pidfile="$PIDFILE_DIR/${name}.pid"
    
    if is_process_running "$pidfile"; then
        local pid=$(cat "$pidfile")
        log_message "INFO" "Deteniendo $name (PID: $pid)..."
        
        # Intentar parada graceful
        kill -TERM "$pid" 2>/dev/null
        
        # Esperar hasta 10 segundos
        for i in {1..10}; do
            if ! kill -0 "$pid" 2>/dev/null; then
                log_message "INFO" "$name detenido correctamente"
                rm -f "$pidfile"
                return 0
            fi
            sleep 1
        done
        
        # Si no responde, forzar
        log_message "WARN" "Forzando parada de $name..."
        kill -KILL "$pid" 2>/dev/null
        rm -f "$pidfile"
    else
        log_message "INFO" "$name no está corriendo"
    fi
}

# Función para detener todo el sistema
stop_system() {
    log_message "INFO" "Deteniendo sistema VisiFruit..."
    
    stop_process "main_system"
    
    # Limpiar archivos PID huérfanos
    find "$PIDFILE_DIR" -name "*.pid" -delete 2>/dev/null || true
    
    log_message "INFO" "Sistema detenido completamente"
}

# Función para mostrar estado del sistema
show_status() {
    print_header
    log_message "INFO" "Estado del Sistema VisiFruit:"
    echo ""
    
    local main_pidfile="$PIDFILE_DIR/main_system.pid"
    
    # Estado del sistema principal
    if is_process_running "$main_pidfile"; then
        local pid=$(cat "$main_pidfile")
        echo -e "${GREEN}✅ Sistema Principal${NC}: Corriendo (PID: $pid)"
        
        # Verificar si los puertos responden
        if curl -s http://localhost:8000/health >/dev/null 2>&1; then
            echo -e "${GREEN}✅ API Principal${NC}: http://localhost:8000 (Respondiendo)"
        else
            echo -e "${YELLOW}⚠️ API Principal${NC}: http://localhost:8000 (No responde)"
        fi
        
        if curl -s http://localhost:8001/health >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Dashboard Backend${NC}: http://localhost:8001 (Respondiendo)"
        else
            echo -e "${YELLOW}⚠️ Dashboard Backend${NC}: http://localhost:8001 (No responde)"
        fi
        
        if curl -s http://localhost:3000 >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Frontend React${NC}: http://localhost:3000 (Respondiendo)"
        else
            echo -e "${YELLOW}⚠️ Frontend React${NC}: http://localhost:3000 (No responde)"
        fi
    else
        echo -e "${RED}❌ Sistema Principal${NC}: No está corriendo"
    fi
    
    echo ""
    echo -e "${CYAN}📊 URLs Disponibles:${NC}"
    echo -e "   • Sistema Principal: ${WHITE}http://localhost:8000${NC}"
    echo -e "   • Dashboard Backend: ${WHITE}http://localhost:8001${NC}"
    echo -e "   • Frontend React: ${WHITE}http://localhost:3000${NC}"
    echo -e "   • Documentación API: ${WHITE}http://localhost:8000/docs${NC}"
    echo ""
}

# Función para mostrar logs en tiempo real
show_logs() {
    local service=${1:-"main_system"}
    local logfile="$LOG_DIR/${service}.log"
    
    if [[ -f "$logfile" ]]; then
        log_message "INFO" "Mostrando logs de $service (Ctrl+C para salir)..."
        tail -f "$logfile"
    else
        log_message "ERROR" "Archivo de log no encontrado: $logfile"
        return 1
    fi
}

# Función para limpiar logs antiguos
cleanup_logs() {
    log_message "INFO" "Limpiando logs antiguos (>7 días)..."
    find "$LOG_DIR" -name "*.log" -type f -mtime +7 -delete 2>/dev/null || true
    log_message "INFO" "Limpieza de logs completada"
}

# Función para backup de configuración
backup_config() {
    local backup_dir="$PROJECT_ROOT/backups"
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_file="$backup_dir/config_backup_$timestamp.tar.gz"
    
    mkdir -p "$backup_dir"
    
    log_message "INFO" "Creando backup de configuración..."
    tar -czf "$backup_file" .env Config_Etiquetadora.json 2>/dev/null || true
    
    if [[ -f "$backup_file" ]]; then
        log_message "INFO" "Backup creado: $backup_file"
    else
        log_message "ERROR" "Error creando backup"
        return 1
    fi
}

# Función para mostrar ayuda
show_help() {
    print_header
    echo -e "${WHITE}Uso: $0 [COMANDO] [OPCIONES]${NC}"
    echo ""
    echo -e "${CYAN}Comandos disponibles:${NC}"
    echo -e "  ${GREEN}start${NC}          Iniciar sistema completo"
    echo -e "  ${GREEN}stop${NC}           Detener sistema completo"
    echo -e "  ${GREEN}restart${NC}        Reiniciar sistema completo"
    echo -e "  ${GREEN}status${NC}         Mostrar estado del sistema"
    echo -e "  ${GREEN}logs${NC}           Mostrar logs en tiempo real"
    echo -e "  ${GREEN}cleanup${NC}        Limpiar logs antiguos"
    echo -e "  ${GREEN}backup${NC}         Backup de configuración"
    echo -e "  ${GREEN}check${NC}          Verificar dependencias"
    echo -e "  ${GREEN}help${NC}           Mostrar esta ayuda"
    echo ""
    echo -e "${CYAN}Opciones:${NC}"
    echo -e "  ${YELLOW}--force${NC}        Forzar parada de procesos en puertos ocupados"
    echo -e "  ${YELLOW}--no-frontend${NC}  No iniciar frontend (solo backend y sistema principal)"
    echo -e "  ${YELLOW}--debug${NC}        Modo debug con logs detallados"
    echo ""
    echo -e "${CYAN}Ejemplos:${NC}"
    echo -e "  $0 start --force"
    echo -e "  $0 logs main_system"
    echo -e "  $0 status"
    echo ""
}

# Función principal
main() {
    local command=${1:-"help"}
    local force_flag=false
    
    # Procesar argumentos
    while [[ $# -gt 0 ]]; do
        case $1 in
            --force)
                force_flag=true
                shift
                ;;
            --debug)
                set -x
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                if [[ -z "$command" || "$command" == "help" ]]; then
                    command=$1
                fi
                shift
                ;;
        esac
    done
    
    case $command in
        start)
            print_header
            log_message "INFO" "Iniciando sistema VisiFruit Ultra v3.0..."
            
            # Verificaciones previas
            create_env_file || exit 1
            check_dependencies || exit 1
            check_gpio_hardware
            
            if [[ "$force_flag" == true ]]; then
                check_ports --force
            else
                check_ports
            fi
            
            # Iniciar sistema
            start_main_system || exit 1
            
            log_message "INFO" "Sistema iniciado correctamente"
            echo ""
            show_status
            ;;
        stop)
            print_header
            stop_system
            ;;
        restart)
            print_header
            log_message "INFO" "Reiniciando sistema..."
            stop_system
            sleep 3
            main start "$@"
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs "$2"
            ;;
        cleanup)
            cleanup_logs
            ;;
        backup)
            backup_config
            ;;
        check)
            print_header
            create_env_file
            check_dependencies
            check_gpio_hardware
            check_ports
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_message "ERROR" "Comando desconocido: $command"
            show_help
            exit 1
            ;;
    esac
}

# Manejo de señales
trap 'echo -e "\n${YELLOW}Interrumpido por usuario${NC}"; exit 130' INT
trap 'stop_system; exit 143' TERM

# Ejecutar función principal
main "$@"
