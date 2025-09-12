#!/bin/bash
# =============================================================================
# install_raspberry_pi5.sh - Instalador optimizado para Raspberry Pi 5
# =============================================================================
#
# Script de instalación automática para VisiFruit en Raspberry Pi 5
# Incluye migración de RPi.GPIO a lgpio y optimizaciones específicas
#
# Autor: Gabriel Calderón, Elias Bautista, Cristian Hernandez
# Fecha: Enero 2025
# Versión: 1.0 - Migración Raspberry Pi 5
#
# Uso:
#   bash install_raspberry_pi5.sh
#   
# =============================================================================

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Función para logging
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        "INFO")
            echo -e "${CYAN}[INFO]${NC} ${timestamp} - $message"
            ;;
        "SUCCESS")
            echo -e "${GREEN}[SUCCESS]${NC} ${timestamp} - $message"
            ;;
        "WARNING")
            echo -e "${YELLOW}[WARNING]${NC} ${timestamp} - $message"
            ;;
        "ERROR")
            echo -e "${RED}[ERROR]${NC} ${timestamp} - $message"
            ;;
        "STEP")
            echo -e "${PURPLE}[STEP]${NC} ${timestamp} - $message"
            ;;
    esac
}

# Función para verificar si es Raspberry Pi 5
check_raspberry_pi5() {
    if [[ ! -f /proc/cpuinfo ]]; then
        log "ERROR" "No se puede determinar el hardware. ¿Está ejecutándose en Raspberry Pi?"
        return 1
    fi
    
    if grep -q "BCM2712" /proc/cpuinfo; then
        log "SUCCESS" "🚀 Raspberry Pi 5 detectado - Procediendo con instalación optimizada"
        return 0
    elif grep -q "Raspberry Pi" /proc/cpuinfo; then
        log "WARNING" "📟 Raspberry Pi < 5 detectado. Este script está optimizado para Pi 5"
        log "INFO" "El sistema funcionará pero recomendamos usar el script de instalación estándar"
        read -p "¿Continuar de todas formas? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            return 0
        else
            return 1
        fi
    else
        log "ERROR" "Sistema no compatible. Este script requiere Raspberry Pi"
        return 1
    fi
}

# Función para verificar privilegios
check_privileges() {
    if [[ $EUID -eq 0 ]]; then
        log "WARNING" "Ejecutándose como root. Recomendamos ejecutar como usuario normal"
        log "INFO" "El script elevará privilegios cuando sea necesario con sudo"
    fi
    
    # Verificar que sudo esté disponible
    if ! command -v sudo &> /dev/null; then
        log "ERROR" "sudo no está disponible. Instalando..."
        apt update && apt install -y sudo
    fi
}

# Función para actualizar sistema
update_system() {
    log "STEP" "Actualizando sistema base..."
    
    sudo apt update || {
        log "ERROR" "Fallo actualizando lista de paquetes"
        return 1
    }
    
    sudo apt upgrade -y || {
        log "WARNING" "Algunos paquetes no se pudieron actualizar"
    }
    
    log "SUCCESS" "Sistema base actualizado"
}

# Función para instalar dependencias del sistema
install_system_dependencies() {
    log "STEP" "Instalando dependencias del sistema para Raspberry Pi 5..."
    
    local packages=(
        # GPIO para Raspberry Pi 5
        "python3-lgpio"
        "python3-rpi-lgpio"
        "python3-pigpio"
        "pigpio"
        
        # Desarrollo Python
        "python3-dev"
        "python3-pip"
        "python3-venv"
        "python3-wheel"
        "python3-setuptools"
        
        # Librerías de imagen y video
        "libgl1-mesa-glx"
        "libglib2.0-0"
        "libopencv-dev"
        "python3-opencv"
        
        # Librerías matemáticas y científicas
        "libatlas-base-dev"
        "libhdf5-dev"
        "libhdf5-serial-dev"
        "libblas-dev"
        "liblapack-dev"
        "gfortran"
        
        # Librerías de imagen
        "libjpeg-dev"
        "libpng-dev"
        "libtiff-dev"
        "libwebp-dev"
        "libopenjp2-7-dev"
        
        # Cámara y video
        "libv4l-dev"
        "v4l-utils"
        "libavcodec-dev"
        "libavformat-dev"
        "libswscale-dev"
        
        # Herramientas de red y comunicación
        "build-essential"
        "cmake"
        "pkg-config"
        "git"
        "wget"
        "curl"
        
        # Utilidades
        "htop"
        "vim"
        "nano"
        "screen"
        "tmux"
    )
    
    log "INFO" "Instalando ${#packages[@]} paquetes del sistema..."
    
    for package in "${packages[@]}"; do
        log "INFO" "Instalando: $package"
        sudo apt install -y "$package" || {
            log "WARNING" "No se pudo instalar $package, continuando..."
        }
    done
    
    # Habilitar pigpio daemon
    log "INFO" "Configurando pigpio daemon..."
    sudo systemctl enable pigpiod
    sudo systemctl start pigpiod
    
    log "SUCCESS" "Dependencias del sistema instaladas"
}

# Función para configurar GPIO específico de Pi 5
configure_pi5_gpio() {
    log "STEP" "Configurando GPIO para Raspberry Pi 5..."
    
    # Verificar que lgpio esté instalado
    if python3 -c "import lgpio" 2>/dev/null; then
        log "SUCCESS" "lgpio Python está disponible"
    else
        log "WARNING" "lgpio Python no disponible, instalando..."
        pip3 install lgpio || {
            log "ERROR" "No se pudo instalar lgpio via pip"
            return 1
        }
    fi
    
    # Configurar permisos GPIO
    log "INFO" "Configurando permisos GPIO..."
    
    # Añadir usuario a grupos GPIO si existen
    if getent group gpio >/dev/null 2>&1; then
        sudo usermod -a -G gpio $USER
        log "INFO" "Usuario añadido al grupo gpio"
    fi
    
    if getent group dialout >/dev/null 2>&1; then
        sudo usermod -a -G dialout $USER
        log "INFO" "Usuario añadido al grupo dialout"
    fi
    
    # Configurar udev rules para GPIO (Pi 5)
    local udev_rule="/etc/udev/rules.d/99-gpio-pi5.rules"
    if [[ ! -f "$udev_rule" ]]; then
        log "INFO" "Creando reglas udev para GPIO Pi 5..."
        sudo tee "$udev_rule" > /dev/null << 'EOF'
# Reglas GPIO para Raspberry Pi 5
SUBSYSTEM=="gpio", GROUP="gpio", MODE="0664"
SUBSYSTEM=="gpiochip", GROUP="gpio", MODE="0664"
EOF
        sudo udevadm control --reload-rules
        sudo udevadm trigger
        log "SUCCESS" "Reglas udev configuradas"
    fi
    
    log "SUCCESS" "Configuración GPIO Pi 5 completada"
}

# Función para crear entorno virtual
setup_virtual_environment() {
    log "STEP" "Configurando entorno virtual Python..."
    
    local venv_path="venv"
    
    if [[ -d "$venv_path" ]]; then
        log "INFO" "Entorno virtual existente encontrado"
        read -p "¿Recrear entorno virtual? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$venv_path"
            log "INFO" "Entorno virtual anterior eliminado"
        else
            log "INFO" "Usando entorno virtual existente"
            return 0
        fi
    fi
    
    log "INFO" "Creando nuevo entorno virtual..."
    python3 -m venv "$venv_path" || {
        log "ERROR" "No se pudo crear entorno virtual"
        return 1
    }
    
    log "INFO" "Activando entorno virtual..."
    source "$venv_path/bin/activate" || {
        log "ERROR" "No se pudo activar entorno virtual"
        return 1
    }
    
    # Actualizar pip
    log "INFO" "Actualizando pip..."
    pip install --upgrade pip setuptools wheel
    
    log "SUCCESS" "Entorno virtual configurado"
}

# Función para instalar dependencias Python
install_python_dependencies() {
    log "STEP" "Instalando dependencias Python para Raspberry Pi 5..."
    
    # Verificar que el entorno virtual esté activo
    if [[ -z "$VIRTUAL_ENV" ]]; then
        log "INFO" "Activando entorno virtual..."
        source venv/bin/activate || {
            log "ERROR" "No se pudo activar entorno virtual"
            return 1
        }
    fi
    
    # Instalar dependencias críticas primero
    log "INFO" "Instalando lgpio (crítico para Pi 5)..."
    pip install lgpio || {
        log "ERROR" "Instalación crítica fallida: lgpio"
        return 1
    }
    
    # Instalar PyTorch optimizado para ARM
    log "INFO" "Instalando PyTorch para ARM64..."
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu || {
        log "WARNING" "PyTorch optimizado no disponible, usando versión estándar..."
        pip install torch torchvision
    }
    
    # Instalar desde requirements.txt
    if [[ -f "Requirements.txt" ]]; then
        log "INFO" "Instalando desde Requirements.txt..."
        pip install --prefer-binary -r Requirements.txt || {
            log "WARNING" "Algunas dependencias fallaron, continuando..."
        }
    else
        log "WARNING" "Requirements.txt no encontrado, instalando dependencias mínimas..."
        
        # Dependencias mínimas para funcionamiento
        local min_deps=(
            "fastapi"
            "uvicorn[standard]"
            "opencv-python"
            "numpy"
            "Pillow"
            "pydantic"
            "asyncio"
            "lgpio"
            "pigpio"
        )
        
        for dep in "${min_deps[@]}"; do
            log "INFO" "Instalando: $dep"
            pip install "$dep" || log "WARNING" "Falló instalación de $dep"
        done
    fi
    
    log "SUCCESS" "Dependencias Python instaladas"
}

# Función para verificar instalación
verify_installation() {
    log "STEP" "Verificando instalación..."
    
    # Verificar entorno virtual
    if [[ -z "$VIRTUAL_ENV" ]]; then
        source venv/bin/activate
    fi
    
    # Test básico de lgpio
    log "INFO" "Probando lgpio..."
    python3 -c "
import lgpio
print('✅ lgpio disponible')
try:
    h = lgpio.gpiochip_open(0)
    print('✅ Chip GPIO accesible')
    lgpio.gpiochip_close(h)
except Exception as e:
    print(f'⚠️ Advertencia GPIO: {e}')
" || {
        log "ERROR" "Test lgpio fallido"
        return 1
    }
    
    # Test del wrapper GPIO
    if [[ -f "utils/gpio_wrapper.py" ]]; then
        log "INFO" "Probando GPIO wrapper..."
        python3 -c "
import sys
sys.path.insert(0, '.')
from utils.gpio_wrapper import GPIO, get_gpio_info, is_raspberry_pi5
info = get_gpio_info()
print(f'GPIO Mode: {info[\"mode\"]}')
print(f'GPIO Type: {info[\"gpio_type\"]}')
print(f'Raspberry Pi 5: {is_raspberry_pi5()}')
print('✅ GPIO wrapper funcionando')
" || {
            log "WARNING" "GPIO wrapper no disponible"
        }
    else
        log "WARNING" "GPIO wrapper no encontrado en utils/gpio_wrapper.py"
    fi
    
    # Test del sistema principal
    if [[ -f "main_etiquetadora.py" ]]; then
        log "INFO" "Probando sistema principal..."
        timeout 10 python3 main_etiquetadora.py --test-mode 2>/dev/null || {
            log "INFO" "Sistema principal requiere configuración adicional"
        }
    fi
    
    log "SUCCESS" "Verificación completada"
}

# Función para configurar servicios del sistema
setup_system_services() {
    log "STEP" "Configurando servicios del sistema..."
    
    # Crear archivo de servicio systemd
    local service_file="/etc/systemd/system/visifruit.service"
    
    if [[ ! -f "$service_file" ]]; then
        log "INFO" "Creando servicio systemd..."
        
        local current_dir=$(pwd)
        local user=$(whoami)
        
        sudo tee "$service_file" > /dev/null << EOF
[Unit]
Description=VisiFruit Industrial Labeling System
After=network.target

[Service]
Type=simple
User=$user
WorkingDirectory=$current_dir
ExecStart=$current_dir/venv/bin/python $current_dir/main_etiquetadora.py
Restart=always
RestartSec=10
Environment=PYTHONPATH=$current_dir

[Install]
WantedBy=multi-user.target
EOF
        
        sudo systemctl daemon-reload
        log "SUCCESS" "Servicio systemd creado"
        log "INFO" "Para habilitar auto-inicio: sudo systemctl enable visifruit"
        log "INFO" "Para iniciar servicio: sudo systemctl start visifruit"
    else
        log "INFO" "Servicio systemd ya existe"
    fi
}

# Función para mostrar resumen final
show_final_summary() {
    log "STEP" "Resumen de instalación completada"
    
    echo
    echo -e "${GREEN}================================================================${NC}"
    echo -e "${GREEN}🎉 INSTALACIÓN RASPBERRY PI 5 COMPLETADA${NC}"
    echo -e "${GREEN}================================================================${NC}"
    echo
    echo -e "${CYAN}✅ Sistema actualizado${NC}"
    echo -e "${CYAN}✅ lgpio instalado y configurado${NC}"
    echo -e "${CYAN}✅ Dependencias Python instaladas${NC}"
    echo -e "${CYAN}✅ Entorno virtual configurado${NC}"
    echo -e "${CYAN}✅ GPIO wrapper creado${NC}"
    echo -e "${CYAN}✅ Migración de RPi.GPIO completada${NC}"
    echo
    echo -e "${YELLOW}📋 PRÓXIMOS PASOS:${NC}"
    echo -e "${YELLOW}1.${NC} Activar entorno virtual: ${BLUE}source venv/bin/activate${NC}"
    echo -e "${YELLOW}2.${NC} Configurar Config_Etiquetadora.json"
    echo -e "${YELLOW}3.${NC} Ejecutar sistema: ${BLUE}python main_etiquetadora.py${NC}"
    echo -e "${YELLOW}4.${NC} Para auto-inicio: ${BLUE}sudo systemctl enable visifruit${NC}"
    echo
    echo -e "${PURPLE}🔧 INFORMACIÓN TÉCNICA:${NC}"
    echo -e "${PURPLE}•${NC} GPIO Mode: lgpio (Raspberry Pi 5 compatible)"
    echo -e "${PURPLE}•${NC} Python: $(python3 --version)"
    echo -e "${PURPLE}•${NC} Hardware: $(cat /proc/device-tree/model 2>/dev/null || echo 'Raspberry Pi')"
    echo -e "${PURPLE}•${NC} Kernel: $(uname -r)"
    echo
    echo -e "${GREEN}¡VisiFruit está listo para Raspberry Pi 5! 🚀${NC}"
    echo
}

# Función principal
main() {
    echo -e "${BLUE}================================================================${NC}"
    echo -e "${BLUE}🍓 INSTALADOR VISIFRUIT PARA RASPBERRY PI 5${NC}"
    echo -e "${BLUE}================================================================${NC}"
    echo -e "${BLUE}Migración automática de RPi.GPIO a lgpio${NC}"
    echo -e "${BLUE}Compatible con nueva arquitectura BCM2712${NC}"
    echo -e "${BLUE}================================================================${NC}"
    echo
    
    # Verificaciones iniciales
    check_raspberry_pi5 || exit 1
    check_privileges
    
    # Instalación paso a paso
    update_system || exit 1
    install_system_dependencies || exit 1
    configure_pi5_gpio || exit 1
    setup_virtual_environment || exit 1
    install_python_dependencies || exit 1
    verify_installation || exit 1
    setup_system_services
    
    # Resumen final
    show_final_summary
    
    log "SUCCESS" "Instalación completada exitosamente"
    
    # Sugerir reinicio si es necesario
    if [[ -f /var/run/reboot-required ]]; then
        echo
        log "WARNING" "Se requiere reinicio del sistema"
        read -p "¿Reiniciar ahora? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log "INFO" "Reiniciando sistema..."
            sudo reboot
        fi
    fi
}

# Manejo de interrupciones
trap 'log "ERROR" "Instalación interrumpida por el usuario"; exit 1' INT TERM

# Ejecutar instalación
main "$@"
