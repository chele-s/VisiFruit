#!/bin/bash

# ========================================================================
# VisiFruit v3.0 - Optimizador de Rendimiento para Raspberry Pi 5
# Optimizaciones específicas para RT-DETR y procesamiento de video
# ========================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

LOG_FILE="/tmp/visifruit_optimizer.log"

# System paths
BOOT_CONFIG="/boot/firmware/config.txt"
CMDLINE="/boot/firmware/cmdline.txt"

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
    esac
    
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
}

print_header() {
    clear
    echo -e "${BLUE}"
    echo "════════════════════════════════════════════════════════════════"
    echo "          ⚡ VisiFruit Performance Optimizer for Pi 5"
    echo "                RT-DETR & Video Processing Tuned"
    echo "════════════════════════════════════════════════════════════════"
    echo -e "${NC}\n"
}

# Optimize CPU performance
optimize_cpu() {
    log "STEP" "Optimizando configuración de CPU..."
    
    # Set CPU governor to performance
    log "INFO" "Configurando gobernador de CPU a 'performance'..."
    
    # Create cpufreq configuration
    cat > /etc/default/cpufrequtils << 'EOF'
# CPU frequency scaling governor
GOVERNOR="performance"
ENABLE="true"
MIN_SPEED="0"
MAX_SPEED="0"
EOF
    
    # Create systemd service for CPU governor
    cat > /etc/systemd/system/cpu-performance.service << 'EOF'
[Unit]
Description=Set CPU Performance Governor
After=multi-user.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/bin/bash -c 'for gov in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do echo performance > $gov; done'

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl enable cpu-performance.service
    
    log "SUCCESS" "Optimizaciones de CPU aplicadas"
}

# Optimize GPU and memory
optimize_gpu() {
    log "STEP" "Optimizando GPU y memoria..."
    
    # Backup original config
    if [[ ! -f "${BOOT_CONFIG}.backup" ]]; then
        cp "$BOOT_CONFIG" "${BOOT_CONFIG}.backup"
        log "INFO" "Backup de config.txt creado"
    fi
    
    # GPU optimizations for Pi 5
    log "INFO" "Configurando GPU para Pi 5..."
    
    # Add GPU optimizations
    cat >> "$BOOT_CONFIG" << 'EOF'

# VisiFruit GPU Optimizations for Pi 5
gpu_mem=256
gpu_freq=750
start_x=1
EOF
    
    log "SUCCESS" "Optimizaciones de GPU aplicadas"
}

# Create monitoring tools
create_monitoring() {
    log "STEP" "Creando herramientas de monitoreo..."
    
    # Performance monitoring script
    cat > /usr/local/bin/visifruit-monitor << 'EOF'
#!/bin/bash

# VisiFruit System Monitor

print_system_info() {
    echo "════════════════════════════════════════════════════════════════"
    echo "                    VisiFruit System Monitor"
    echo "════════════════════════════════════════════════════════════════"
    echo "Timestamp: $(date)"
    echo ""
    
    # Temperature
    local cpu_temp=$(vcgencmd measure_temp | cut -d= -f2)
    echo "🌡️  CPU Temperature: $cpu_temp"
    
    # Memory
    free -h | grep -E "(Mem|Swap):" | while read line; do
        echo "🧠 $line"
    done
    
    # GPU memory
    local gpu_mem=$(vcgencmd get_mem gpu)
    echo "🎮 GPU Memory: $gpu_mem"
    
    # Load average
    local load=$(uptime | awk -F'load average:' '{print $2}')
    echo "📊 Load Average:$load"
    
    # Services
    echo ""
    echo "🔧 VisiFruit Services:"
    for service in visifruit visifruit-backend nginx; do
        status=$(systemctl is-active "$service" 2>/dev/null || echo "inactive")
        case $status in
            "active") echo "   ✅ $service: $status" ;;
            "inactive") echo "   ❌ $service: $status" ;;
            *) echo "   ⚠️  $service: $status" ;;
        esac
    done
    
    echo ""
    echo "════════════════════════════════════════════════════════════════"
}

case "$1" in
    continuous)
        while true; do
            clear
            print_system_info
            sleep 5
        done
        ;;
    *)
        print_system_info
        echo ""
        echo "Uso: $0 [continuous]"
        echo "  continuous  - Monitoreo continuo (Ctrl+C para salir)"
        ;;
esac
EOF
    
    chmod +x /usr/local/bin/visifruit-monitor
    
    # Performance tuning script
    cat > /usr/local/bin/visifruit-tune << 'EOF'
#!/bin/bash

# VisiFruit Performance Tuning Script

case "$1" in
    max-performance)
        echo "Aplicando máximo rendimiento..."
        # CPU to performance mode
        for gov in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
            echo performance > "$gov" 2>/dev/null || true
        done
        echo "✅ Modo máximo rendimiento activado"
        ;;
    balanced)
        echo "Aplicando modo balanceado..."
        for gov in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
            echo ondemand > "$gov" 2>/dev/null || true
        done
        echo "✅ Modo balanceado activado"
        ;;
    status)
        echo "Estado actual del sistema:"
        echo "=========================="
        echo "CPU Governor: $(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor)"
        echo "Temperature: $(vcgencmd measure_temp)"
        echo "GPU Memory: $(vcgencmd get_mem gpu)"
        ;;
    *)
        echo "Uso: $0 {max-performance|balanced|status}"
        ;;
esac
EOF
    
    chmod +x /usr/local/bin/visifruit-tune
    
    log "SUCCESS" "Herramientas de monitoreo creadas"
}

# Main execution
main() {
    print_header
    
    if [[ $EUID -ne 0 ]]; then
        log "ERROR" "Este script debe ejecutarse como root (sudo)"
        exit 1
    fi
    
    log "INFO" "VisiFruit Performance Optimizer para Raspberry Pi 5"
    echo ""
    
    read -p "¿Continuar con las optimizaciones? (y/N): " -r
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
    
    # Apply optimizations
    log "INFO" "Iniciando optimizaciones del sistema..."
    
    optimize_cpu
    optimize_gpu
    create_monitoring
    
    # Reload systemd
    systemctl daemon-reload
    
    echo ""
    log "SUCCESS" "Optimizaciones completadas exitosamente"
    echo ""
    echo -e "${CYAN}Nuevos comandos disponibles:${NC}"
    echo -e "  • ${YELLOW}visifruit-monitor${NC}        - Monitor del sistema"
    echo -e "  • ${YELLOW}visifruit-monitor continuous${NC} - Monitor continuo"
    echo -e "  • ${YELLOW}visifruit-tune status${NC}    - Estado del rendimiento"
    echo -e "  • ${YELLOW}visifruit-tune max-performance${NC} - Máximo rendimiento"
    echo ""
}

# Execute main function
main "$@"
