#!/bin/bash
# ============================================================================
# 🛠️ VisiFruit Sistema - Instalador y Configurador Automático
# ============================================================================
# Script para instalar dependencias y configurar el sistema VisiFruit
# en Raspberry Pi 5 desde cero
# 
# Autor: Gabriel Calderón, Elias Bautista, Cristian Hernandez
# Fecha: Julio 2025
# Versión: 3.0.0-ULTRA
# ============================================================================

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

print_header() {
    echo -e "${CYAN}"
    echo "=============================================="
    echo "  🛠️  VisiFruit Instalador Automático v3.0"
    echo "=============================================="
    echo -e "${NC}"
}

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
        "SUCCESS")
            echo -e "${GREEN}[SUCCESS]${NC} [$timestamp] $message"
            ;;
        *)
            echo -e "${WHITE}[LOG]${NC} [$timestamp] $message"
            ;;
    esac
}

# Verificar si se ejecuta como root para ciertas operaciones
check_sudo() {
    if [[ $EUID -eq 0 ]]; then
        log_message "WARN" "Ejecutándose como root - Algunas operaciones se harán como usuario normal"
        return 0
    fi
    return 1
}

# Actualizar sistema
update_system() {
    log_message "INFO" "Actualizando sistema..."
    
    if command -v apt-get &> /dev/null; then
        sudo apt-get update -y
        sudo apt-get upgrade -y
        log_message "SUCCESS" "Sistema actualizado"
    else
        log_message "WARN" "apt-get no disponible - omitiendo actualización"
    fi
}

# Instalar dependencias del sistema
install_system_dependencies() {
    log_message "INFO" "Instalando dependencias del sistema..."
    
    local packages=(
        "python3"
        "python3-pip"
        "python3-venv"
        "python3-dev"
        "build-essential"
        "git"
        "curl"
        "wget"
        "lsof"
        "htop"
        "nano"
        "tree"
        "unzip"
        "tar"
        "gzip"
        "libopencv-dev"
        "python3-opencv"
        "libjpeg-dev"
        "libpng-dev"
        "libtiff-dev"
        "libgstreamer1.0-dev"
        "libgstreamer-plugins-base1.0-dev"
        "libgtk-3-dev"
        "libcairo2-dev"
        "libpango1.0-dev"
        "libgdk-pixbuf2.0-dev"
        "libffi-dev"
        "libssl-dev"
    )
    
    for package in "${packages[@]}"; do
        if ! dpkg -l | grep -q "^ii  $package "; then
            log_message "INFO" "Instalando $package..."
            sudo apt-get install -y "$package" || log_message "WARN" "Error instalando $package"
        else
            log_message "INFO" "$package ya está instalado"
        fi
    done
    
    log_message "SUCCESS" "Dependencias del sistema instaladas"
}

# Instalar Node.js y npm
install_nodejs() {
    log_message "INFO" "Verificando Node.js..."
    
    if command -v node &> /dev/null; then
        local version=$(node --version)
        log_message "INFO" "Node.js ya instalado: $version"
        
        # Verificar si es una versión reciente
        if [[ ${version:1:2} -ge 16 ]]; then
            log_message "SUCCESS" "Versión de Node.js es suficiente"
            return 0
        fi
    fi
    
    log_message "INFO" "Instalando Node.js 18..."
    
    # Instalar Node.js 18
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
    
    if command -v node &> /dev/null; then
        local version=$(node --version)
        log_message "SUCCESS" "Node.js instalado: $version"
    else
        log_message "ERROR" "Error instalando Node.js"
        return 1
    fi
}

# Crear entorno virtual Python
setup_python_env() {
    log_message "INFO" "Configurando entorno virtual Python..."
    
    cd "$PROJECT_ROOT"
    
    if [[ ! -d "venv" ]]; then
        log_message "INFO" "Creando entorno virtual..."
        python3 -m venv venv
        log_message "SUCCESS" "Entorno virtual creado"
    else
        log_message "INFO" "Entorno virtual ya existe"
    fi
    
    # Activar entorno virtual
    source venv/bin/activate
    
    # Actualizar pip
    log_message "INFO" "Actualizando pip..."
    pip install --upgrade pip
    
    # Instalar dependencias Python
    if [[ -f "requirements.txt" ]]; then
        log_message "INFO" "Instalando dependencias Python..."
        pip install -r requirements.txt
        log_message "SUCCESS" "Dependencias Python instaladas"
    elif [[ -f "Requirements.txt" ]]; then
        log_message "INFO" "Instalando dependencias Python..."
        pip install -r Requirements.txt
        log_message "SUCCESS" "Dependencias Python instaladas"
    else
        log_message "WARN" "requirements.txt no encontrado - instalando dependencias básicas"
        pip install fastapi uvicorn numpy opencv-python pillow
    fi
    
    deactivate
}

# Instalar dependencias GPIO para Raspberry Pi 5
install_gpio_dependencies() {
    log_message "INFO" "Configurando dependencias GPIO para Raspberry Pi 5..."
    
    # Verificar si estamos en Raspberry Pi
    if [[ -f /proc/device-tree/model ]]; then
        local model=$(cat /proc/device-tree/model)
        if [[ $model == *"Raspberry Pi 5"* ]]; then
            log_message "INFO" "Raspberry Pi 5 detectado - Instalando lgpio..."
            
            # Activar entorno virtual
            source "$PROJECT_ROOT/venv/bin/activate"
            
            # Instalar lgpio
            pip install lgpio
            
            # Instalar otras dependencias GPIO
            pip install RPi.GPIO adafruit-circuitpython-motor adafruit-circuitpython-servo
            
            deactivate
            
            log_message "SUCCESS" "Dependencias GPIO instaladas"
        else
            log_message "INFO" "No es Raspberry Pi 5 - instalando dependencias estándar"
            source "$PROJECT_ROOT/venv/bin/activate"
            pip install RPi.GPIO
            deactivate
        fi
    else
        log_message "WARN" "Sistema no identificado - omitiendo dependencias GPIO específicas"
    fi
}

# Configurar frontend
setup_frontend() {
    log_message "INFO" "Configurando frontend React..."
    
    local frontend_dir="$PROJECT_ROOT/Interfaz_Usuario/VisiFruit"
    
    if [[ -d "$frontend_dir" ]]; then
        cd "$frontend_dir"
        
        if [[ -f "package.json" ]]; then
            log_message "INFO" "Instalando dependencias del frontend..."
            npm install
            
            if [[ $? -eq 0 ]]; then
                log_message "SUCCESS" "Frontend configurado correctamente"
            else
                log_message "ERROR" "Error configurando frontend"
                return 1
            fi
        else
            log_message "WARN" "package.json no encontrado en frontend"
        fi
    else
        log_message "WARN" "Directorio del frontend no encontrado"
    fi
    
    cd "$PROJECT_ROOT"
}

# Crear archivo de configuración .env
create_env_file() {
    log_message "INFO" "Configurando archivo .env..."
    
    cd "$PROJECT_ROOT"
    
    if [[ ! -f ".env" ]]; then
        if [[ -f "env_config_template.txt" ]]; then
            cp "env_config_template.txt" ".env"
            log_message "SUCCESS" "Archivo .env creado desde template"
        else
            log_message "WARN" "Template no encontrado - creando .env básico"
            cat > .env << EOL
# Configuración básica VisiFruit
FRUPRINT_ENV=production
NODE_ENV=production
DEBUG_MODE=false
LOG_LEVEL=INFO

# Servidores
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=8001
FRONTEND_HOST=0.0.0.0
FRONTEND_PORT=3000

# URLs
VITE_API_URL=http://localhost:8001
VITE_WS_URL=ws://localhost:8001/ws/realtime
VITE_MAIN_API_URL=http://localhost:8000

# Auto-inicio
AUTO_START_FRONTEND=true
AUTO_START_BACKEND=true
AUTO_START_MAIN_SYSTEM=true
EOL
            log_message "SUCCESS" "Archivo .env básico creado"
        fi
    else
        log_message "INFO" "Archivo .env ya existe"
    fi
}

# Configurar permisos GPIO
setup_gpio_permissions() {
    log_message "INFO" "Configurando permisos GPIO..."
    
    # Agregar usuario al grupo gpio
    if groups | grep -q gpio; then
        log_message "INFO" "Usuario ya está en grupo gpio"
    else
        sudo usermod -a -G gpio $USER
        log_message "SUCCESS" "Usuario agregado al grupo gpio"
        log_message "WARN" "Reinicia la sesión para aplicar cambios de grupo"
    fi
    
    # Configurar udev rules para acceso GPIO sin sudo
    sudo tee /etc/udev/rules.d/99-gpio.rules > /dev/null << EOL
KERNEL=="gpiochip*", GROUP="gpio", MODE="0660"
KERNEL=="gpio*", GROUP="gpio", MODE="0660"
EOL
    
    log_message "SUCCESS" "Reglas udev configuradas"
}

# Crear directorios necesarios
create_directories() {
    log_message "INFO" "Creando directorios necesarios..."
    
    local dirs=(
        "$PROJECT_ROOT/logs"
        "$PROJECT_ROOT/logs/categories"
        "$PROJECT_ROOT/logs/performance"
        "$PROJECT_ROOT/logs/errors"
        "$PROJECT_ROOT/data"
        "$PROJECT_ROOT/backups"
        "$PROJECT_ROOT/.pids"
    )
    
    for dir in "${dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            log_message "INFO" "Creado: $dir"
        fi
    done
    
    log_message "SUCCESS" "Directorios creados"
}

# Crear servicio systemd (opcional)
create_systemd_service() {
    if [[ "$1" == "--service" ]]; then
        log_message "INFO" "Creando servicio systemd..."
        
        sudo tee /etc/systemd/system/visifruit.service > /dev/null << EOL
[Unit]
Description=VisiFruit Sistema Industrial de Etiquetado
After=network.target

[Service]
Type=forking
User=$USER
WorkingDirectory=$PROJECT_ROOT
ExecStart=$PROJECT_ROOT/start_visifruit_system.sh start
ExecStop=$PROJECT_ROOT/start_visifruit_system.sh stop
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOL
        
        sudo systemctl daemon-reload
        sudo systemctl enable visifruit.service
        
        log_message "SUCCESS" "Servicio systemd creado"
        log_message "INFO" "Usa 'sudo systemctl start visifruit' para iniciar como servicio"
    fi
}

# Verificar instalación
verify_installation() {
    log_message "INFO" "Verificando instalación..."
    
    local errors=0
    
    # Verificar Python
    if [[ -f "$PROJECT_ROOT/venv/bin/python" ]]; then
        log_message "SUCCESS" "✅ Entorno Python configurado"
    else
        log_message "ERROR" "❌ Entorno Python no encontrado"
        ((errors++))
    fi
    
    # Verificar dependencias Python
    source "$PROJECT_ROOT/venv/bin/activate"
    if python -c "import fastapi, uvicorn" 2>/dev/null; then
        log_message "SUCCESS" "✅ Dependencias Python OK"
    else
        log_message "ERROR" "❌ Dependencias Python faltantes"
        ((errors++))
    fi
    deactivate
    
    # Verificar Node.js
    if command -v npm &> /dev/null; then
        log_message "SUCCESS" "✅ Node.js/npm disponible"
    else
        log_message "ERROR" "❌ Node.js/npm no encontrado"
        ((errors++))
    fi
    
    # Verificar frontend
    if [[ -d "$PROJECT_ROOT/Interfaz_Usuario/VisiFruit/node_modules" ]]; then
        log_message "SUCCESS" "✅ Frontend configurado"
    else
        log_message "WARN" "⚠️ Frontend no completamente configurado"
    fi
    
    # Verificar archivo .env
    if [[ -f "$PROJECT_ROOT/.env" ]]; then
        log_message "SUCCESS" "✅ Archivo .env presente"
    else
        log_message "ERROR" "❌ Archivo .env faltante"
        ((errors++))
    fi
    
    if [[ $errors -eq 0 ]]; then
        log_message "SUCCESS" "🎉 Instalación completada correctamente"
        return 0
    else
        log_message "ERROR" "❌ Instalación completada con $errors errores"
        return 1
    fi
}

# Mostrar información final
show_final_info() {
    echo ""
    echo -e "${CYAN}=============================================="
    echo "  🎉 Instalación Completada"
    echo "=============================================="
    echo -e "${NC}"
    echo -e "${GREEN}El sistema VisiFruit está listo para usar!${NC}"
    echo ""
    echo -e "${CYAN}Comandos disponibles:${NC}"
    echo -e "  ${WHITE}./start_visifruit_system.sh start${NC}   - Iniciar sistema completo"
    echo -e "  ${WHITE}./start_visifruit_system.sh status${NC}  - Ver estado del sistema"
    echo -e "  ${WHITE}./start_visifruit_system.sh stop${NC}    - Detener sistema"
    echo -e "  ${WHITE}./start_visifruit_system.sh help${NC}    - Ver ayuda completa"
    echo ""
    echo -e "${CYAN}URLs del sistema (una vez iniciado):${NC}"
    echo -e "  • Sistema Principal: ${WHITE}http://localhost:8000${NC}"
    echo -e "  • Dashboard Backend: ${WHITE}http://localhost:8001${NC}"
    echo -e "  • Frontend React: ${WHITE}http://localhost:3000${NC}"
    echo -e "  • Documentación API: ${WHITE}http://localhost:8000/docs${NC}"
    echo ""
    echo -e "${YELLOW}Nota: Si instalaste como servicio systemd, usa:${NC}"
    echo -e "  ${WHITE}sudo systemctl start visifruit${NC}"
    echo ""
}

# Función principal
main() {
    print_header
    
    log_message "INFO" "Iniciando instalación automática de VisiFruit..."
    
    # Verificar argumentos
    local install_service=false
    if [[ "$1" == "--service" ]]; then
        install_service=true
        log_message "INFO" "Instalación como servicio systemd solicitada"
    fi
    
    # Pasos de instalación
    log_message "INFO" "Paso 1/10: Actualizando sistema..."
    update_system
    
    log_message "INFO" "Paso 2/10: Instalando dependencias del sistema..."
    install_system_dependencies
    
    log_message "INFO" "Paso 3/10: Instalando Node.js..."
    install_nodejs
    
    log_message "INFO" "Paso 4/10: Configurando entorno Python..."
    setup_python_env
    
    log_message "INFO" "Paso 5/10: Instalando dependencias GPIO..."
    install_gpio_dependencies
    
    log_message "INFO" "Paso 6/10: Configurando frontend..."
    setup_frontend
    
    log_message "INFO" "Paso 7/10: Creando archivo de configuración..."
    create_env_file
    
    log_message "INFO" "Paso 8/10: Configurando permisos GPIO..."
    setup_gpio_permissions
    
    log_message "INFO" "Paso 9/10: Creando directorios..."
    create_directories
    
    if [[ "$install_service" == true ]]; then
        log_message "INFO" "Paso 10/10: Creando servicio systemd..."
        create_systemd_service --service
    else
        log_message "INFO" "Paso 10/10: Finalizando..."
    fi
    
    # Verificar instalación
    verify_installation
    
    if [[ $? -eq 0 ]]; then
        show_final_info
    else
        log_message "ERROR" "Instalación completada con errores - revisa los logs"
        return 1
    fi
}

# Ejecutar
main "$@"
