#!/bin/bash
# start_pigpio_daemon.sh
# Script para iniciar y verificar el daemon pigpio para control de servos MG995
# Autor: Gabriel Calderón, Elias Bautista, Cristian Hernandez
# Versión: 1.0

echo "🚀 VisiFruit - Inicializador de Daemon Pigpio"
echo "=============================================="
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para verificar si pigpio está instalado
check_pigpio_installed() {
    if ! command -v pigpiod &> /dev/null; then
        echo -e "${RED}❌ pigpio no está instalado${NC}"
        echo ""
        echo "Para instalar pigpio:"
        echo "  sudo apt update"
        echo "  sudo apt install -y pigpio python3-pigpio"
        echo ""
        return 1
    fi
    return 0
}

# Función para verificar si el daemon está corriendo
check_daemon_running() {
    if pgrep -x "pigpiod" > /dev/null; then
        return 0
    else
        return 1
    fi
}

# Función para obtener PID del daemon
get_daemon_pid() {
    pgrep -x "pigpiod"
}

# Función para iniciar el daemon
start_daemon() {
    echo -e "${BLUE}🔧 Iniciando daemon pigpio...${NC}"
    
    # Iniciar daemon con opciones recomendadas
    # -s 10: sample rate 10μs (mejor precisión para servos)
    sudo pigpiod -s 10
    
    # Esperar a que inicie
    sleep 1
    
    if check_daemon_running; then
        PID=$(get_daemon_pid)
        echo -e "${GREEN}✅ Daemon pigpio iniciado correctamente (PID: $PID)${NC}"
        return 0
    else
        echo -e "${RED}❌ Error iniciando daemon pigpio${NC}"
        return 1
    fi
}

# Función para detener el daemon
stop_daemon() {
    echo -e "${YELLOW}⏹️ Deteniendo daemon pigpio...${NC}"
    sudo killall pigpiod 2>/dev/null
    sleep 1
    
    if ! check_daemon_running; then
        echo -e "${GREEN}✅ Daemon pigpio detenido${NC}"
        return 0
    else
        echo -e "${RED}❌ No se pudo detener el daemon${NC}"
        return 1
    fi
}

# Función para reiniciar el daemon
restart_daemon() {
    echo -e "${BLUE}🔄 Reiniciando daemon pigpio...${NC}"
    stop_daemon
    sleep 1
    start_daemon
}

# Función para mostrar estado
show_status() {
    echo -e "${BLUE}📊 Estado del Daemon Pigpio${NC}"
    echo "=============================="
    
    if check_daemon_running; then
        PID=$(get_daemon_pid)
        echo -e "Estado: ${GREEN}CORRIENDO${NC}"
        echo "PID: $PID"
        
        # Mostrar información adicional
        if [ -f "/proc/$PID/cmdline" ]; then
            CMDLINE=$(tr '\0' ' ' < /proc/$PID/cmdline)
            echo "Comando: $CMDLINE"
        fi
        
        # Verificar si python puede conectarse
        echo ""
        echo "Verificando conectividad Python..."
        python3 -c "
import pigpio
try:
    pi = pigpio.pi()
    if pi.connected:
        print('✅ Python puede conectarse al daemon')
        print(f'   Versión hardware: {pi.get_hardware_revision()}')
        print(f'   Versión pigpio: {pi.get_pigpio_version()}')
        pi.stop()
    else:
        print('❌ Python NO puede conectarse')
except Exception as e:
    print(f'❌ Error: {e}')
" 2>/dev/null
        
    else
        echo -e "Estado: ${RED}NO CORRIENDO${NC}"
        echo ""
        echo "Para iniciar: $0 start"
    fi
}

# Función de ayuda
show_help() {
    echo "Uso: $0 [comando]"
    echo ""
    echo "Comandos:"
    echo "  start     - Inicia el daemon pigpio"
    echo "  stop      - Detiene el daemon pigpio"
    echo "  restart   - Reinicia el daemon pigpio"
    echo "  status    - Muestra el estado del daemon"
    echo "  help      - Muestra esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0 start"
    echo "  $0 status"
    echo ""
}

# Main
main() {
    # Verificar que pigpio está instalado
    if ! check_pigpio_installed; then
        exit 1
    fi
    
    # Procesar comando
    COMMAND=${1:-status}
    
    case "$COMMAND" in
        start)
            if check_daemon_running; then
                PID=$(get_daemon_pid)
                echo -e "${YELLOW}⚠️ Daemon pigpio ya está corriendo (PID: $PID)${NC}"
                echo "Usa '$0 restart' para reiniciarlo"
                exit 0
            else
                start_daemon
                exit $?
            fi
            ;;
        
        stop)
            if check_daemon_running; then
                stop_daemon
                exit $?
            else
                echo -e "${YELLOW}⚠️ Daemon pigpio no está corriendo${NC}"
                exit 0
            fi
            ;;
        
        restart)
            restart_daemon
            exit $?
            ;;
        
        status)
            show_status
            exit 0
            ;;
        
        help|--help|-h)
            show_help
            exit 0
            ;;
        
        *)
            echo -e "${RED}❌ Comando desconocido: $COMMAND${NC}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Ejecutar main
main "$@"

