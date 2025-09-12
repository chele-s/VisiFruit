#!/bin/bash

# ========================================================================
# VisiFruit v3.0 RT-DETR - Instalador para Raspberry Pi 5
# Sistema Industrial de Etiquetado de Frutas con IA
# Compatibilidad: Raspberry Pi OS (Debian 12 Bookworm) - Raspberry Pi 5
# ========================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Configuration
VISIFRUIT_USER="visifruit"
VISIFRUIT_HOME="/home/$VISIFRUIT_USER"
VISIFRUIT_DIR="$VISIFRUIT_HOME/VisiFruit"
PYTHON_VERSION="3.11"
VENV_PATH="$VISIFRUIT_DIR/venv"
LOG_FILE="/tmp/visifruit_install.log"

# System information
PI_MODEL=$(tr -d '\0' < /proc/device-tree/model 2>/dev/null || echo "Unknown")
OS_VERSION=$(lsb_release -d | cut -f2-)
KERNEL_VERSION=$(uname -r)
TOTAL_RAM=$(free -h | awk '/^Mem:/ {print $2}')
CPU_INFO=$(lscpu | grep "Model name" | cut -d: -f2 | xargs)

# Logging function
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        "INFO")
            echo -e "${GREEN}[INFO]${NC} $message"
            ;;
        "WARN") 
            echo -e "${YELLOW}[WARN]${NC} $message"
            ;;
        "ERROR")
            echo -e "${RED}[ERROR]${NC} $message"
            ;;
        "SUCCESS")
            echo -e "${GREEN}[SUCCESS]${NC} $message"
            ;;
        "STEP")
            echo -e "${CYAN}[STEP]${NC} $message"
            ;;
    esac
    
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
}

# Header
print_header() {
    clear
    echo -e "${PURPLE}"
    echo "════════════════════════════════════════════════════════════════"
    echo "                    🍓 VisiFruit v3.0 RT-DETR"
    echo "           Sistema Industrial de Etiquetado de Frutas"
    echo "                Instalador para Raspberry Pi 5"
    echo "════════════════════════════════════════════════════════════════"
    echo -e "${NC}"
    echo -e "${WHITE}Información del Sistema:${NC}"
    echo -e "  📱 Dispositivo: ${CYAN}$PI_MODEL${NC}"
    echo -e "  🐧 OS: ${CYAN}$OS_VERSION${NC}"
    echo -e "  🔧 Kernel: ${CYAN}$KERNEL_VERSION${NC}"
    echo -e "  🧠 RAM: ${CYAN}$TOTAL_RAM${NC}"
    echo -e "  ⚡ CPU: ${CYAN}$CPU_INFO${NC}"
    echo ""
}

# Check if running on Raspberry Pi 5
check_hardware() {
    log "STEP" "Verificando compatibilidad de hardware..."
    
    if [[ ! "$PI_MODEL" =~ "Raspberry Pi 5" ]]; then
        log "ERROR" "Este instalador está optimizado para Raspberry Pi 5"
        log "ERROR" "Dispositivo detectado: $PI_MODEL"
        log "WARN" "¿Desea continuar de todos modos? (y/N)"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        log "SUCCESS" "Raspberry Pi 5 detectado correctamente"
    fi
    
    # Check if running as root
    if [[ $EUID -ne 0 ]]; then
        log "ERROR" "Este script debe ejecutarse como root (sudo)"
        exit 1
    fi
    
    # Check available space
    local available_space=$(df / | awk 'NR==2 {print $4}')
    if [[ $available_space -lt 8388608 ]]; then  # 8GB in KB
        log "WARN" "Espacio disponible limitado. Se recomiendan al menos 8GB libres"
    fi
}

# Create user and directories
setup_user() {
    log "STEP" "Configurando usuario del sistema..."
    
    if ! id "$VISIFRUIT_USER" &>/dev/null; then
        log "INFO" "Creando usuario $VISIFRUIT_USER..."
        useradd -m -s /bin/bash -G gpio,i2c,spi,video,audio,plugdev "$VISIFRUIT_USER"
        
        # Set password
        echo -e "${YELLOW}Configura una contraseña para el usuario $VISIFRUIT_USER:${NC}"
        passwd "$VISIFRUIT_USER"
    else
        log "INFO" "Usuario $VISIFRUIT_USER ya existe"
        usermod -a -G gpio,i2c,spi,video,audio,plugdev "$VISIFRUIT_USER"
    fi
    
    # Create directories
    sudo -u "$VISIFRUIT_USER" mkdir -p "$VISIFRUIT_HOME"/{logs,config,models,data}
    chown -R "$VISIFRUIT_USER:$VISIFRUIT_USER" "$VISIFRUIT_HOME"
    
    log "SUCCESS" "Usuario y directorios configurados"
}

# Update system and install base packages
install_system_dependencies() {
    log "STEP" "Actualizando sistema e instalando dependencias..."
    
    # Update package lists
    log "INFO" "Actualizando listas de paquetes..."
    apt update
    
    # Upgrade system
    log "INFO" "Actualizando sistema (esto puede tardar varios minutos)..."
    apt upgrade -y
    
    # Install essential packages
    log "INFO" "Instalando dependencias esenciales..."
    apt install -y \
        curl \
        wget \
        git \
        build-essential \
        cmake \
        pkg-config \
        unzip \
        software-properties-common \
        apt-transport-https \
        ca-certificates \
        gnupg \
        lsb-release
    
    # Install Python and development tools
    log "INFO" "Instalando Python $PYTHON_VERSION y herramientas de desarrollo..."
    apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        python3-setuptools \
        python3-wheel \
        python3-distutils
    
    # Install multimedia and imaging libraries
    log "INFO" "Instalando librerías multimedia e imaging..."
    apt install -y \
        libopencv-dev \
        python3-opencv \
        libgl1-mesa-glx \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender-dev \
        libgomp1 \
        libatlas-base-dev \
        libhdf5-dev \
        libhdf5-serial-dev \
        libjpeg-dev \
        libpng-dev \
        libtiff-dev \
        libwebp-dev \
        libopenjp2-7-dev \
        libilmbase-dev \
        libopenexr-dev \
        libavcodec-dev \
        libavformat-dev \
        libswscale-dev \
        libv4l-dev \
        v4l-utils \
        libdc1394-dev \
        libgstreamer1.0-dev \
        libgstreamer-plugins-base1.0-dev
    
    # Install GPIO and hardware libraries
    log "INFO" "Instalando librerías GPIO y hardware..."
    apt install -y \
        python3-rpi.gpio \
        python3-pigpio \
        pigpio \
        i2c-tools \
        python3-smbus \
        python3-spidev
    
    # Install networking and web tools
    log "INFO" "Instalando herramientas de red y web..."
    apt install -y \
        nginx \
        supervisor \
        redis-server \
        sqlite3 \
        postgresql-client \
        nodejs \
        npm
    
    # Install monitoring tools
    log "INFO" "Instalando herramientas de monitoreo..."
    apt install -y \
        htop \
        iotop \
        glances \
        tree \
        screen \
        tmux
    
    # Install development tools
    log "INFO" "Instalando herramientas de desarrollo..."
    apt install -y \
        vim \
        nano \
        git-lfs \
        jq \
        rsync
    
    log "SUCCESS" "Dependencias del sistema instaladas"
}

# Configure hardware interfaces
configure_hardware() {
    log "STEP" "Configurando interfaces de hardware..."
    
    # Enable camera interface
    log "INFO" "Habilitando interfaz de cámara..."
    if ! grep -q "^camera_auto_detect=1" /boot/firmware/config.txt; then
        echo "camera_auto_detect=1" >> /boot/firmware/config.txt
    fi
    
    # Enable I2C
    log "INFO" "Habilitando I2C..."
    if ! grep -q "^dtparam=i2c_arm=on" /boot/firmware/config.txt; then
        echo "dtparam=i2c_arm=on" >> /boot/firmware/config.txt
    fi
    
    # Enable SPI
    log "INFO" "Habilitando SPI..."
    if ! grep -q "^dtparam=spi=on" /boot/firmware/config.txt; then
        echo "dtparam=spi=on" >> /boot/firmware/config.txt
    fi
    
    # Enable GPIO
    log "INFO" "Configurando GPIO..."
    if ! grep -q "^gpio=" /boot/firmware/config.txt; then
        echo "# GPIO Configuration for VisiFruit" >> /boot/firmware/config.txt
        echo "gpio=2-27=op,dh" >> /boot/firmware/config.txt
    fi
    
    # Configure GPU memory for camera
    log "INFO" "Configurando memoria GPU para cámara..."
    if ! grep -q "^gpu_mem=" /boot/firmware/config.txt; then
        echo "gpu_mem=128" >> /boot/firmware/config.txt
    fi
    
    # Enable pigpio daemon
    log "INFO" "Configurando servicio pigpio..."
    systemctl enable pigpiod
    systemctl start pigpiod
    
    log "SUCCESS" "Hardware configurado"
}

# Install VisiFruit project
install_visifruit() {
    log "STEP" "Instalando proyecto VisiFruit..."
    
    # Clone or copy project
    if [[ -d "$VISIFRUIT_DIR" ]]; then
        log "WARN" "Directorio VisiFruit ya existe. ¿Sobrescribir? (y/N)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            rm -rf "$VISIFRUIT_DIR"
        else
            log "INFO" "Manteniendo instalación existente"
            return
        fi
    fi
    
    # Create project directory
    sudo -u "$VISIFRUIT_USER" mkdir -p "$VISIFRUIT_DIR"
    
    # Copy current directory content (assuming script is run from VisiFruit directory)
    if [[ -f "README.md" && -f "main_etiquetadora.py" ]]; then
        log "INFO" "Copiando archivos del proyecto..."
        cp -r . "$VISIFRUIT_DIR/"
        chown -R "$VISIFRUIT_USER:$VISIFRUIT_USER" "$VISIFRUIT_DIR"
    else
        log "ERROR" "No se encontraron archivos del proyecto en el directorio actual"
        log "ERROR" "Ejecute este script desde el directorio raíz de VisiFruit"
        exit 1
    fi
    
    log "SUCCESS" "Proyecto VisiFruit instalado"
}

# Setup Python environment
setup_python_environment() {
    log "STEP" "Configurando entorno Python..."
    
    # Create virtual environment
    log "INFO" "Creando entorno virtual..."
    sudo -u "$VISIFRUIT_USER" python3 -m venv "$VENV_PATH"
    
    # Upgrade pip
    log "INFO" "Actualizando pip..."
    sudo -u "$VISIFRUIT_USER" "$VENV_PATH/bin/pip" install --upgrade pip setuptools wheel
    
    # Install PyTorch for ARM64 (optimized for Pi 5)
    log "INFO" "Instalando PyTorch optimizado para ARM64..."
    sudo -u "$VISIFRUIT_USER" "$VENV_PATH/bin/pip" install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
    
    # Install RT-DETR dependencies
    log "INFO" "Instalando dependencias RT-DETR..."
    
    # Try PaddlePaddle first (if available for ARM64)
    log "INFO" "Intentando instalar PaddlePaddle..."
    if sudo -u "$VISIFRUIT_USER" "$VENV_PATH/bin/pip" install paddlepaddle-cpu paddledet 2>/dev/null; then
        log "SUCCESS" "PaddlePaddle instalado exitosamente"
    else
        log "WARN" "PaddlePaddle no disponible para ARM64, usando PyTorch backend"
    fi
    
    # Install transformers and related packages
    sudo -u "$VISIFRUIT_USER" "$VENV_PATH/bin/pip" install \
        transformers \
        datasets \
        accelerate \
        ultralytics
    
    # Install main requirements
    log "INFO" "Instalando dependencias principales..."
    if [[ -f "$VISIFRUIT_DIR/Requirements.txt" ]]; then
        sudo -u "$VISIFRUIT_USER" "$VENV_PATH/bin/pip" install -r "$VISIFRUIT_DIR/Requirements.txt" --prefer-binary
    fi
    
    log "SUCCESS" "Entorno Python configurado"
}

# Optimize system for VisiFruit
optimize_system() {
    log "STEP" "Optimizando sistema para VisiFruit..."
    
    # Increase swap (important for compilation)
    log "INFO" "Configurando swap..."
    if [[ ! -f /swapfile ]] || [[ $(stat -c%s /swapfile) -lt 2147483648 ]]; then
        # Create 2GB swap
        fallocate -l 2G /swapfile
        chmod 600 /swapfile
        mkswap /swapfile
        swapon /swapfile
        
        # Make permanent
        if ! grep -q '/swapfile' /etc/fstab; then
            echo '/swapfile none swap sw 0 0' >> /etc/fstab
        fi
    fi
    
    # Configure GPU memory split
    log "INFO" "Optimizando memoria GPU..."
    sed -i 's/^gpu_mem=.*/gpu_mem=256/' /boot/firmware/config.txt 2>/dev/null || echo "gpu_mem=256" >> /boot/firmware/config.txt
    
    # Set CPU governor to performance
    log "INFO" "Configurando gobernador CPU..."
    echo 'GOVERNOR="performance"' > /etc/default/cpufrequtils
    
    # Optimize I/O scheduler
    log "INFO" "Optimizando planificador I/O..."
    echo 'ACTION=="add|change", KERNEL=="sd[a-z]", ATTR{queue/scheduler}="deadline"' > /etc/udev/rules.d/60-ioschedulers.rules
    
    # Configure automatic temperature monitoring
    log "INFO" "Configurando monitoreo de temperatura..."
    cat > /usr/local/bin/temp_monitor.sh << 'EOF'
#!/bin/bash
TEMP=$(vcgencmd measure_temp | cut -d= -f2 | cut -d"'" -f1)
if (( $(echo "$TEMP > 80" | bc -l) )); then
    logger "WARNING: High CPU temperature: ${TEMP}°C"
fi
EOF
    chmod +x /usr/local/bin/temp_monitor.sh
    
    # Add cron job for temperature monitoring
    if ! crontab -l 2>/dev/null | grep -q temp_monitor; then
        (crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/temp_monitor.sh") | crontab -
    fi
    
    log "SUCCESS" "Sistema optimizado"
}

# Configure camera
configure_camera() {
    log "STEP" "Configurando cámara..."
    
    # Test camera detection
    log "INFO" "Detectando cámaras disponibles..."
    
    # Check for libcamera
    if command -v libcamera-hello &> /dev/null; then
        log "INFO" "Probando cámara con libcamera..."
        if timeout 10s libcamera-hello --timeout 1000 --nopreview 2>/dev/null; then
            log "SUCCESS" "Cámara CSI detectada y funcionando"
        fi
    fi
    
    # Check for USB cameras
    if ls /dev/video* &>/dev/null; then
        log "INFO" "Cámaras USB detectadas:"
        for camera in /dev/video*; do
            if [[ -c "$camera" ]]; then
                local camera_info=$(v4l2-ctl --device="$camera" --info 2>/dev/null | grep "Card type" | cut -d: -f2 | xargs)
                log "INFO" "  $camera: $camera_info"
            fi
        done
    fi
    
    # Create camera configuration
    cat > "$VISIFRUIT_DIR/config/camera_config.json" << EOF
{
    "camera": {
        "type": "auto_detect",
        "resolution": [1920, 1080],
        "fps": 30,
        "auto_exposure": true,
        "buffer_size": 3,
        "format": "MJPG"
    },
    "detection": {
        "input_size": [640, 640],
        "confidence_threshold": 0.5,
        "nms_threshold": 0.4
    }
}
EOF
    
    chown "$VISIFRUIT_USER:$VISIFRUIT_USER" "$VISIFRUIT_DIR/config/camera_config.json"
    
    log "SUCCESS" "Cámara configurada"
}

# Create systemd services
create_services() {
    log "STEP" "Creando servicios del sistema..."
    
    # Main VisiFruit service
    cat > /etc/systemd/system/visifruit.service << EOF
[Unit]
Description=VisiFruit v3.0 RT-DETR Industrial Fruit Labeling System
After=network.target pigpiod.service
Wants=pigpiod.service

[Service]
Type=simple
User=$VISIFRUIT_USER
WorkingDirectory=$VISIFRUIT_DIR
Environment=PATH=$VENV_PATH/bin
ExecStart=$VENV_PATH/bin/python main_etiquetadora.py
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=visifruit

# Resource limits
MemoryMax=2G
CPUQuota=200%

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=$VISIFRUIT_HOME

[Install]
WantedBy=multi-user.target
EOF

    # Backend service
    cat > /etc/systemd/system/visifruit-backend.service << EOF
[Unit]
Description=VisiFruit Backend API
After=network.target

[Service]
Type=simple
User=$VISIFRUIT_USER
WorkingDirectory=$VISIFRUIT_DIR/Interfaz_Usuario/Backend
Environment=PATH=$VENV_PATH/bin
ExecStart=$VENV_PATH/bin/python main.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    # Nginx configuration for frontend
    cat > /etc/nginx/sites-available/visifruit << EOF
server {
    listen 80;
    server_name localhost;
    
    # Frontend static files
    location / {
        root $VISIFRUIT_DIR/Interfaz_Usuario/VisiFruit/dist;
        try_files \$uri \$uri/ /index.html;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # WebSocket
    location /ws {
        proxy_pass http://localhost:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
    }
}
EOF
    
    # Enable nginx site
    ln -sf /etc/nginx/sites-available/visifruit /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    
    # Reload systemd and enable services
    systemctl daemon-reload
    systemctl enable visifruit.service
    systemctl enable visifruit-backend.service
    systemctl enable nginx
    
    log "SUCCESS" "Servicios creados y habilitados"
}

# Build frontend
build_frontend() {
    log "STEP" "Construyendo frontend..."
    
    cd "$VISIFRUIT_DIR/Interfaz_Usuario/VisiFruit"
    
    # Install Node.js dependencies
    log "INFO" "Instalando dependencias de Node.js..."
    sudo -u "$VISIFRUIT_USER" npm install
    
    # Build production version
    log "INFO" "Construyendo versión de producción..."
    sudo -u "$VISIFRUIT_USER" npm run build
    
    chown -R "$VISIFRUIT_USER:$VISIFRUIT_USER" "$VISIFRUIT_DIR/Interfaz_Usuario/VisiFruit"
    
    log "SUCCESS" "Frontend construido"
}

# Create management scripts
create_management_scripts() {
    log "STEP" "Creando scripts de gestión..."
    
    # Main control script
    cat > /usr/local/bin/visifruit << 'EOF'
#!/bin/bash

# VisiFruit Management Script

case "$1" in
    start)
        echo "Iniciando VisiFruit..."
        sudo systemctl start visifruit-backend
        sudo systemctl start visifruit
        sudo systemctl start nginx
        echo "VisiFruit iniciado"
        ;;
    stop)
        echo "Deteniendo VisiFruit..."
        sudo systemctl stop visifruit
        sudo systemctl stop visifruit-backend
        sudo systemctl stop nginx
        echo "VisiFruit detenido"
        ;;
    restart)
        echo "Reiniciando VisiFruit..."
        sudo systemctl restart visifruit-backend
        sudo systemctl restart visifruit
        sudo systemctl restart nginx
        echo "VisiFruit reiniciado"
        ;;
    status)
        echo "Estado de VisiFruit:"
        sudo systemctl status visifruit --no-pager -l
        sudo systemctl status visifruit-backend --no-pager -l
        sudo systemctl status nginx --no-pager -l
        ;;
    logs)
        echo "Logs de VisiFruit:"
        sudo journalctl -u visifruit -f
        ;;
    update)
        echo "Actualizando VisiFruit..."
        cd /home/visifruit/VisiFruit
        sudo -u visifruit git pull
        sudo -u visifruit /home/visifruit/VisiFruit/venv/bin/pip install -r Requirements.txt
        cd /home/visifruit/VisiFruit/Interfaz_Usuario/VisiFruit
        sudo -u visifruit npm install
        sudo -u visifruit npm run build
        sudo systemctl restart visifruit-backend
        sudo systemctl restart visifruit
        echo "VisiFruit actualizado"
        ;;
    *)
        echo "Uso: $0 {start|stop|restart|status|logs|update}"
        exit 1
        ;;
esac
EOF
    
    chmod +x /usr/local/bin/visifruit
    
    # System info script
    cat > /usr/local/bin/visifruit-info << 'EOF'
#!/bin/bash

echo "========================="
echo "VisiFruit System Info"
echo "========================="
echo "Dispositivo: $(tr -d '\0' < /proc/device-tree/model)"
echo "OS: $(lsb_release -d | cut -f2-)"
echo "Kernel: $(uname -r)"
echo "CPU: $(lscpu | grep "Model name" | cut -d: -f2 | xargs)"
echo "RAM: $(free -h | awk '/^Mem:/ {print $2}')"
echo "Temperatura CPU: $(vcgencmd measure_temp)"
echo "GPU Memory: $(vcgencmd get_mem gpu)"
echo "========================="
echo "Cámaras disponibles:"
ls -la /dev/video* 2>/dev/null || echo "No se detectaron cámaras USB"
if command -v libcamera-hello &>/dev/null; then
    echo "libcamera disponible: Sí"
else
    echo "libcamera disponible: No"
fi
echo "========================="
echo "Estado de servicios:"
systemctl is-active visifruit
systemctl is-active visifruit-backend
systemctl is-active nginx
systemctl is-active pigpiod
EOF
    
    chmod +x /usr/local/bin/visifruit-info
    
    log "SUCCESS" "Scripts de gestión creados"
}

# Final configuration and test
final_setup() {
    log "STEP" "Configuración final y pruebas..."
    
    # Set permissions
    chown -R "$VISIFRUIT_USER:$VISIFRUIT_USER" "$VISIFRUIT_DIR"
    
    # Create desktop shortcut
    if [[ -d "/home/$VISIFRUIT_USER/Desktop" ]]; then
        cat > "/home/$VISIFRUIT_USER/Desktop/VisiFruit.desktop" << EOF
[Desktop Entry]
Name=VisiFruit Controller
Comment=Sistema de Control VisiFruit
Exec=lxterminal -e 'visifruit status; bash'
Icon=applications-engineering
Terminal=true
Type=Application
Categories=Application;
EOF
        
        chown "$VISIFRUIT_USER:$VISIFRUIT_USER" "/home/$VISIFRUIT_USER/Desktop/VisiFruit.desktop"
        chmod +x "/home/$VISIFRUIT_USER/Desktop/VisiFruit.desktop"
    fi
    
    # Test basic functionality
    log "INFO" "Probando instalación básica..."
    
    if sudo -u "$VISIFRUIT_USER" "$VENV_PATH/bin/python" -c "import torch; print(f'PyTorch: {torch.__version__}')"; then
        log "SUCCESS" "PyTorch funcionando correctamente"
    else
        log "ERROR" "Problema con PyTorch"
    fi
    
    if sudo -u "$VISIFRUIT_USER" "$VENV_PATH/bin/python" -c "import cv2; print(f'OpenCV: {cv2.__version__}')"; then
        log "SUCCESS" "OpenCV funcionando correctamente"
    else
        log "ERROR" "Problema con OpenCV"
    fi
    
    # Test camera
    if ls /dev/video* &>/dev/null; then
        log "SUCCESS" "Cámaras USB detectadas"
    fi
    
    log "SUCCESS" "Configuración final completada"
}

# Main installation flow
main() {
    print_header
    
    log "INFO" "Iniciando instalación de VisiFruit v3.0 RT-DETR"
    log "INFO" "Tiempo estimado: 30-60 minutos"
    echo ""
    
    read -p "¿Desea continuar con la instalación? (y/N): " -r
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "INFO" "Instalación cancelada"
        exit 0
    fi
    
    # Estimate total steps
    local total_steps=12
    local current_step=0
    
    # Step 1
    ((current_step++))
    echo -e "\n${BLUE}[${current_step}/${total_steps}] Verificación de hardware${NC}"
    check_hardware
    
    # Step 2
    ((current_step++))
    echo -e "\n${BLUE}[${current_step}/${total_steps}] Configuración de usuario${NC}"
    setup_user
    
    # Step 3
    ((current_step++))
    echo -e "\n${BLUE}[${current_step}/${total_steps}] Instalación de dependencias del sistema${NC}"
    install_system_dependencies
    
    # Step 4
    ((current_step++))
    echo -e "\n${BLUE}[${current_step}/${total_steps}] Configuración de hardware${NC}"
    configure_hardware
    
    # Step 5
    ((current_step++))
    echo -e "\n${BLUE}[${current_step}/${total_steps}] Instalación del proyecto${NC}"
    install_visifruit
    
    # Step 6
    ((current_step++))
    echo -e "\n${BLUE}[${current_step}/${total_steps}] Configuración del entorno Python${NC}"
    setup_python_environment
    
    # Step 7
    ((current_step++))
    echo -e "\n${BLUE}[${current_step}/${total_steps}] Optimización del sistema${NC}"
    optimize_system
    
    # Step 8
    ((current_step++))
    echo -e "\n${BLUE}[${current_step}/${total_steps}] Configuración de cámara${NC}"
    configure_camera
    
    # Step 9
    ((current_step++))
    echo -e "\n${BLUE}[${current_step}/${total_steps}] Construcción del frontend${NC}"
    build_frontend
    
    # Step 10
    ((current_step++))
    echo -e "\n${BLUE}[${current_step}/${total_steps}] Creación de servicios${NC}"
    create_services
    
    # Step 11
    ((current_step++))
    echo -e "\n${BLUE}[${current_step}/${total_steps}] Scripts de gestión${NC}"
    create_management_scripts
    
    # Step 12
    ((current_step++))
    echo -e "\n${BLUE}[${current_step}/${total_steps}] Configuración final${NC}"
    final_setup
    
    # Installation complete
    echo ""
    echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}           🎉 INSTALACIÓN COMPLETADA EXITOSAMENTE 🎉${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${WHITE}VisiFruit v3.0 RT-DETR ha sido instalado correctamente${NC}"
    echo ""
    echo -e "${CYAN}Comandos disponibles:${NC}"
    echo -e "  • ${YELLOW}visifruit start${NC}     - Iniciar el sistema"
    echo -e "  • ${YELLOW}visifruit stop${NC}      - Detener el sistema"
    echo -e "  • ${YELLOW}visifruit status${NC}    - Ver estado del sistema"
    echo -e "  • ${YELLOW}visifruit logs${NC}      - Ver logs en tiempo real"
    echo -e "  • ${YELLOW}visifruit-info${NC}      - Información del sistema"
    echo ""
    echo -e "${CYAN}Acceso web:${NC}"
    echo -e "  • ${YELLOW}http://$(hostname -I | awk '{print $1}')${NC} - Interfaz web"
    echo -e "  • ${YELLOW}http://localhost${NC} - Desde la misma Pi"
    echo ""
    echo -e "${YELLOW}IMPORTANTE:${NC} ${RED}Es necesario reiniciar para completar la configuración${NC}"
    echo ""
    
    read -p "¿Desea reiniciar ahora? (y/N): " -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log "INFO" "Reiniciando sistema..."
        reboot
    else
        log "WARN" "Recuerde reiniciar manualmente para completar la configuración"
    fi
}

# Execute main function
main "$@"
