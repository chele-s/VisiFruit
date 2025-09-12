#!/bin/bash

# ========================================================================
# VisiFruit v3.0 RT-DETR - Instalador Completo para Raspberry Pi 5
# Script maestro que ejecuta toda la instalación automáticamente
# ========================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
PURPLE='\033[0;35m'
NC='\033[0m'

LOG_FILE="/tmp/visifruit_complete_install.log"
START_TIME=$(date +%s)

# Logging function
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        "INFO") echo -e "${GREEN}[INFO]${NC} $message" ;;
        "WARN") echo -e "${YELLOW}[WARN]${NC} $message" ;;
        "ERROR") echo -e "${RED}[ERROR]${NC} $message" ;;
        "SUCCESS") echo -e "${GREEN}[SUCCESS]${NC} $message" ;;
        "STEP") echo -e "${CYAN}[STEP]${NC} $message" ;;
        "PHASE") echo -e "${PURPLE}[PHASE]${NC} $message" ;;
    esac
    
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
}

# Print beautiful header
print_header() {
    clear
    echo -e "${PURPLE}"
    cat << 'EOF'
════════════════════════════════════════════════════════════════════════════════
                          🍓 VisiFruit v3.0 RT-DETR
                     Sistema Industrial de Etiquetado de Frutas
                        Instalador Completo para Raspberry Pi 5
════════════════════════════════════════════════════════════════════════════════
EOF
    echo -e "${NC}"
    
    echo -e "${WHITE}Bienvenido al Instalador Automático de VisiFruit v3.0${NC}"
    echo -e "${CYAN}Este script instalará todo el sistema completo en su Raspberry Pi 5${NC}"
    echo ""
    
    # System info
    local pi_model=$(tr -d '\0' < /proc/device-tree/model 2>/dev/null || echo "Unknown")
    local os_version=$(lsb_release -d | cut -f2- 2>/dev/null || echo "Unknown")
    local total_ram=$(free -h | awk '/^Mem:/ {print $2}')
    local available_space=$(df -h / | awk 'NR==2 {print $4}')
    
    echo -e "${WHITE}Información del Sistema:${NC}"
    echo -e "  📱 Hardware: ${CYAN}$pi_model${NC}"
    echo -e "  🐧 OS: ${CYAN}$os_version${NC}"
    echo -e "  🧠 RAM: ${CYAN}$total_ram${NC}"
    echo -e "  💾 Espacio Disponible: ${CYAN}$available_space${NC}"
    echo ""
}

# Check prerequisites
check_prerequisites() {
    log "PHASE" "Verificando prerequisitos del sistema..."
    
    # Check if running as root
    if [[ $EUID -ne 0 ]]; then
        log "ERROR" "Este script debe ejecutarse como root (sudo)"
        echo -e "${RED}Uso: sudo $0${NC}"
        exit 1
    fi
    
    # Check if running on Raspberry Pi 5
    local pi_model=$(tr -d '\0' < /proc/device-tree/model 2>/dev/null || echo "Unknown")
    if [[ ! "$pi_model" =~ "Raspberry Pi 5" ]]; then
        log "WARN" "Este instalador está optimizado para Raspberry Pi 5"
        log "WARN" "Dispositivo detectado: $pi_model"
        echo ""
        read -p "¿Desea continuar de todos modos? (y/N): " -r
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log "INFO" "Instalación cancelada por el usuario"
            exit 0
        fi
    fi
    
    # Check available space (minimum 8GB)
    local available_kb=$(df / | awk 'NR==2 {print $4}')
    local available_gb=$((available_kb / 1024 / 1024))
    
    if [[ $available_gb -lt 8 ]]; then
        log "ERROR" "Espacio insuficiente. Disponible: ${available_gb}GB, Requerido: 8GB"
        exit 1
    fi
    
    # Check internet connectivity
    if ! ping -c 1 google.com &>/dev/null; then
        log "ERROR" "Sin conexión a internet. Se requiere conexión para descargar dependencias"
        exit 1
    fi
    
    # Check if project files exist in current directory
    if [[ ! -f "main_etiquetadora.py" ]] || [[ ! -f "README.md" ]]; then
        log "ERROR" "Archivos del proyecto VisiFruit no encontrados en el directorio actual"
        log "ERROR" "Ejecute este script desde el directorio raíz del proyecto VisiFruit"
        exit 1
    fi
    
    log "SUCCESS" "Prerequisitos verificados correctamente"
}

# Show installation plan
show_installation_plan() {
    echo ""
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}                              PLAN DE INSTALACIÓN${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${WHITE}El instalador ejecutará los siguientes pasos:${NC}"
    echo ""
    echo -e "${CYAN}FASE 1: Instalación Base${NC}"
    echo -e "  ✓ Configuración de usuario del sistema"
    echo -e "  ✓ Actualización del sistema operativo"
    echo -e "  ✓ Instalación de dependencias del sistema"
    echo -e "  ✓ Configuración de hardware (GPIO, I2C, SPI, cámara)"
    echo -e "  ✓ Instalación del proyecto VisiFruit"
    echo ""
    echo -e "${CYAN}FASE 2: Entorno Python y IA${NC}"
    echo -e "  ✓ Configuración de entorno virtual Python"
    echo -e "  ✓ Instalación de PyTorch optimizado para ARM64"
    echo -e "  ✓ Instalación de RT-DETR y dependencias"
    echo -e "  ✓ Configuración de modelos RT-DETR"
    echo ""
    echo -e "${CYAN}FASE 3: Configuración Avanzada${NC}"
    echo -e "  ✓ Detección y configuración automática de cámaras"
    echo -e "  ✓ Optimizaciones específicas para Pi 5"
    echo -e "  ✓ Construcción del frontend web"
    echo ""
    echo -e "${WHITE}Tiempo estimado: ${YELLOW}30-60 minutos${NC} (dependiendo del hardware)"
    echo ""
}

# Execute installation phase
execute_phase() {
    local phase_number=$1
    local phase_name="$2"
    local script_name="$3"
    local description="$4"
    
    echo ""
    echo -e "${PURPLE}═══════════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${PURPLE}                      FASE $phase_number: $phase_name${NC}"
    echo -e "${PURPLE}═══════════════════════════════════════════════════════════════════════════════${NC}"
    echo ""
    
    log "PHASE" "Iniciando Fase $phase_number: $phase_name"
    log "INFO" "$description"
    
    if [[ -f "$script_name" ]]; then
        log "INFO" "Ejecutando script: $script_name"
        
        # Make script executable
        chmod +x "$script_name"
        
        # Execute script
        if bash "$script_name"; then
            log "SUCCESS" "Fase $phase_number completada exitosamente"
        else
            log "ERROR" "Fallo en Fase $phase_number: $phase_name"
            log "ERROR" "Verifique el log en $LOG_FILE para más detalles"
            return 1
        fi
    else
        log "ERROR" "Script no encontrado: $script_name"
        return 1
    fi
    
    return 0
}

# Main installation process
run_installation() {
    log "PHASE" "Iniciando instalación completa de VisiFruit v3.0"
    
    local phases=(
        "1;Instalación Base;raspberry_pi5_installer.sh;Instalación base del sistema y dependencias"
        "2;Configuración RT-DETR;install_rtdetr_pi5.sh;Instalación y configuración de RT-DETR"
        "3;Configuración de Cámaras;raspberry_pi5_camera_setup.sh;Detección y configuración de cámaras"
        "4;Optimización del Sistema;raspberry_pi5_optimizer.sh;Optimizaciones específicas para Pi 5"
    )
    
    for phase_info in "${phases[@]}"; do
        IFS=';' read -r phase_num phase_name script_name description <<< "$phase_info"
        
        if ! execute_phase "$phase_num" "$phase_name" "$script_name" "$description"; then
            log "ERROR" "Instalación abortada en Fase $phase_num"
            return 1
        fi
        
        # Small delay between phases
        sleep 2
    done
    
    return 0
}

# Final verification and testing
final_verification() {
    log "PHASE" "Ejecutando verificación final del sistema..."
    
    echo ""
    echo -e "${CYAN}Verificando servicios...${NC}"
    
    # Check services
    local services=("visifruit" "visifruit-backend" "nginx")
    
    for service in "${services[@]}"; do
        if systemctl is-active "$service" &>/dev/null; then
            echo -e "  ✅ $service: ${GREEN}Activo${NC}"
        else
            echo -e "  ❌ $service: ${RED}Inactivo${NC}"
        fi
    done
    
    # Check RT-DETR
    echo ""
    echo -e "${CYAN}Verificando RT-DETR...${NC}"
    if command -v visifruit-rtdetr &>/dev/null; then
        echo -e "  ✅ RT-DETR: ${GREEN}Herramientas instaladas${NC}"
    else
        echo -e "  ❌ RT-DETR: ${RED}No instalado${NC}"
    fi
    
    # Check cameras
    echo ""
    echo -e "${CYAN}Verificando cámaras...${NC}"
    if command -v visifruit-camera &>/dev/null; then
        echo -e "  ✅ Herramientas de cámara: ${GREEN}Instaladas${NC}"
    fi
    
    # Network test
    echo ""
    echo -e "${CYAN}Verificando red...${NC}"
    local ip_address=$(hostname -I | awk '{print $1}')
    if [[ -n "$ip_address" ]]; then
        echo -e "  ✅ IP Address: ${GREEN}$ip_address${NC}"
        echo -e "  ✅ Acceso web: ${GREEN}http://$ip_address${NC}"
    else
        echo -e "  ❌ Red: ${RED}No configurada${NC}"
    fi
    
    return 0
}

# Show final summary
show_final_summary() {
    local end_time=$(date +%s)
    local duration=$((end_time - START_TIME))
    local duration_min=$((duration / 60))
    local duration_sec=$((duration % 60))
    
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}                    🎉 INSTALACIÓN COMPLETADA EXITOSAMENTE 🎉${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════════════${NC}"
    echo ""
    
    echo -e "${WHITE}VisiFruit v3.0 RT-DETR ha sido instalado correctamente en su Raspberry Pi 5${NC}"
    echo -e "${WHITE}Duración total: ${CYAN}${duration_min}m ${duration_sec}s${NC}"
    echo ""
    
    echo -e "${CYAN}🚀 Acceso al Sistema:${NC}"
    local ip_address=$(hostname -I | awk '{print $1}')
    echo -e "  • ${YELLOW}Interfaz Web: http://$ip_address${NC}"
    echo -e "  • ${YELLOW}SSH: ssh visifruit@$ip_address${NC}"
    echo ""
    
    echo -e "${CYAN}⚙️ Comandos Principales:${NC}"
    echo -e "  • ${YELLOW}visifruit start${NC}           - Iniciar sistema"
    echo -e "  • ${YELLOW}visifruit status${NC}          - Ver estado"
    echo -e "  • ${YELLOW}visifruit-rtdetr test${NC}     - Probar RT-DETR"
    echo -e "  • ${YELLOW}visifruit-camera detect${NC}   - Detectar cámaras"
    echo -e "  • ${YELLOW}visifruit-monitor${NC}         - Monitor del sistema"
    echo ""
    
    echo -e "${YELLOW}IMPORTANTE:${NC} ${RED}Se recomienda reiniciar el sistema para aplicar todas las configuraciones${NC}"
    echo ""
    
    read -p "¿Desea reiniciar ahora? (y/N): " -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log "INFO" "Reiniciando sistema por solicitud del usuario..."
        echo -e "${GREEN}Reiniciando en 5 segundos...${NC}"
        sleep 5
        reboot
    else
        echo ""
        echo -e "${GREEN}Para reiniciar manualmente más tarde:${NC}"
        echo -e "  ${YELLOW}sudo reboot${NC}"
    fi
}

# Error handler
handle_error() {
    local exit_code=$?
    local line_number=$1
    
    echo ""
    log "ERROR" "Error en línea $line_number (código: $exit_code)"
    log "ERROR" "Instalación abortada"
    
    echo ""
    echo -e "${RED}═══════════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}                              ERROR EN LA INSTALACIÓN${NC}"
    echo -e "${RED}═══════════════════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${WHITE}La instalación falló en la línea $line_number${NC}"
    echo -e "${WHITE}Código de error: $exit_code${NC}"
    echo ""
    echo -e "${CYAN}Para diagnosticar el problema:${NC}"
    echo -e "  • ${YELLOW}Revisar log: $LOG_FILE${NC}"
    echo ""
    
    exit 1
}

# Set error handler
trap 'handle_error $LINENO' ERR

# Main execution
main() {
    # Initialize
    print_header
    check_prerequisites
    show_installation_plan
    
    # Confirm installation
    echo ""
    read -p "¿Desea continuar con la instalación completa? (y/N): " -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "INFO" "Instalación cancelada por el usuario"
        echo -e "${YELLOW}Instalación cancelada. Para ejecutar más tarde:${NC}"
        echo -e "  ${CYAN}sudo $0${NC}"
        exit 0
    fi
    
    # Start installation
    log "INFO" "Iniciando instalación completa de VisiFruit v3.0 RT-DETR"
    echo ""
    
    # Run installation phases
    if run_installation; then
        # Final verification
        final_verification
        
        # Show summary
        show_final_summary
        
        log "SUCCESS" "Instalación completada exitosamente"
    else
        log "ERROR" "Instalación falló"
        exit 1
    fi
}

# Execute main function
main "$@"
