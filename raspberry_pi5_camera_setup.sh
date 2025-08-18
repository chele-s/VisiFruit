#!/bin/bash

# ========================================================================
# VisiFruit v3.0 - Configuración Avanzada de Cámara para Raspberry Pi 5
# Script de configuración específica para cámaras industriales
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

VISIFRUIT_USER="visifruit"
VISIFRUIT_DIR="/home/$VISIFRUIT_USER/VisiFruit"
LOG_FILE="/tmp/visifruit_camera_setup.log"

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
    esac
    
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
}

print_header() {
    clear
    echo -e "${CYAN}"
    echo "════════════════════════════════════════════════════════════════"
    echo "            🎥 VisiFruit Camera Configuration Tool"
    echo "                 Raspberry Pi 5 Optimized"
    echo "════════════════════════════════════════════════════════════════"
    echo -e "${NC}\n"
}

# Detect available cameras
detect_cameras() {
    log "INFO" "Detectando cámaras disponibles..."
    
    local cameras_found=0
    
    echo -e "${WHITE}Cámaras detectadas:${NC}"
    echo "════════════════════════════════════════════════════════════════"
    
    # Check for CSI cameras using libcamera
    if command -v libcamera-hello &>/dev/null; then
        log "INFO" "Probando cámara CSI con libcamera..."
        if timeout 5s libcamera-hello --list-cameras 2>/dev/null | grep -q "Available cameras"; then
            echo -e "${GREEN}✓ Cámara CSI detectada (libcamera)${NC}"
            libcamera-hello --list-cameras 2>/dev/null | grep -E "(Available cameras|^\[)"
            ((cameras_found++))
        fi
    fi
    
    # Check for USB/V4L2 cameras
    if ls /dev/video* &>/dev/null; then
        for camera in /dev/video*; do
            if [[ -c "$camera" ]]; then
                local camera_info=$(v4l2-ctl --device="$camera" --info 2>/dev/null | grep "Card type" | cut -d: -f2 | xargs)
                local formats=$(v4l2-ctl --device="$camera" --list-formats-ext 2>/dev/null | head -20)
                
                echo -e "${GREEN}✓ $camera: $camera_info${NC}"
                if [[ -n "$formats" ]]; then
                    echo "  Formatos soportados:"
                    echo "$formats" | grep -E "(Index|Size|Interval)" | sed 's/^/    /'
                fi
                ((cameras_found++))
            fi
        done
    fi
    
    echo "════════════════════════════════════════════════════════════════"
    
    if [[ $cameras_found -eq 0 ]]; then
        log "WARN" "No se detectaron cámaras. Verificando configuración..."
        check_camera_configuration
        return 1
    else
        log "SUCCESS" "Se detectaron $cameras_found cámara(s)"
        return 0
    fi
}

# Check camera configuration
check_camera_configuration() {
    log "INFO" "Verificando configuración de cámara..."
    
    # Check if camera interface is enabled
    if grep -q "^camera_auto_detect=1" /boot/firmware/config.txt; then
        echo -e "${GREEN}✓ Interfaz de cámara habilitada${NC}"
    else
        echo -e "${RED}✗ Interfaz de cámara deshabilitada${NC}"
        log "WARN" "Ejecute: echo 'camera_auto_detect=1' | sudo tee -a /boot/firmware/config.txt"
    fi
    
    # Check GPU memory
    local gpu_mem=$(vcgencmd get_mem gpu | cut -d= -f2 | cut -d'M' -f1)
    if [[ $gpu_mem -ge 128 ]]; then
        echo -e "${GREEN}✓ Memoria GPU: ${gpu_mem}MB${NC}"
    else
        echo -e "${YELLOW}⚠ Memoria GPU baja: ${gpu_mem}MB (recomendado: 128MB+)${NC}"
    fi
    
    # Check for libcamera
    if command -v libcamera-hello &>/dev/null; then
        echo -e "${GREEN}✓ libcamera instalado${NC}"
    else
        echo -e "${RED}✗ libcamera no encontrado${NC}"
    fi
    
    # Check V4L2 utilities
    if command -v v4l2-ctl &>/dev/null; then
        echo -e "${GREEN}✓ v4l2-utils instalado${NC}"
    else
        echo -e "${RED}✗ v4l2-utils no encontrado${NC}"
    fi
}

# Create camera test scripts
create_camera_tests() {
    log "INFO" "Creando scripts de prueba de cámara..."
    
    # Create CSI camera test script
    cat > "$VISIFRUIT_DIR/test_csi_camera.py" << 'EOF'
#!/usr/bin/env python3
"""
Test script for CSI camera with libcamera
"""

import subprocess
import sys
import time
import os

def test_libcamera():
    """Test libcamera functionality"""
    print("Testing libcamera...")
    
    try:
        # List cameras
        result = subprocess.run(['libcamera-hello', '--list-cameras'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✓ libcamera can detect cameras")
            print(result.stdout)
        else:
            print("✗ libcamera failed to detect cameras")
            return False
        
        # Test still capture
        print("\nTesting still capture...")
        result = subprocess.run(['libcamera-still', '-o', '/tmp/test_capture.jpg', 
                               '--timeout', '2000', '--nopreview'], 
                              capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0 and os.path.exists('/tmp/test_capture.jpg'):
            print("✓ Still capture successful")
            os.remove('/tmp/test_capture.jpg')
            return True
        else:
            print("✗ Still capture failed")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("✗ libcamera timeout")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    print("VisiFruit CSI Camera Test")
    print("=" * 50)
    
    success = test_libcamera()
    sys.exit(0 if success else 1)
EOF
    
    # Create USB camera test script
    cat > "$VISIFRUIT_DIR/test_usb_cameras.py" << 'EOF'
#!/usr/bin/env python3
"""
Test script for USB cameras
"""

import cv2
import sys
import glob
import json

def find_usb_cameras():
    """Find available USB cameras"""
    cameras = []
    
    # Check /dev/video* devices
    video_devices = glob.glob('/dev/video*')
    for device in video_devices:
        device_num = int(device.split('video')[1])
        
        cap = cv2.VideoCapture(device_num)
        if cap.isOpened():
            # Test if we can actually read frames
            ret, frame = cap.read()
            if ret and frame is not None:
                # Get camera info
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                
                cameras.append({
                    'device': device,
                    'index': device_num,
                    'width': width,
                    'height': height,
                    'fps': fps
                })
            cap.release()
    
    return cameras

def create_camera_config(cameras):
    """Create camera configuration file"""
    config = {
        "cameras": {},
        "default_camera": None
    }
    
    for i, camera in enumerate(cameras):
        camera_id = f"usb_camera_{i}"
        config["cameras"][camera_id] = {
            "type": "usb_webcam",
            "device_id": camera["index"],
            "name": f"USB Camera {i}",
            "resolution": [camera["width"], camera["height"]],
            "fps": int(camera["fps"]) if camera["fps"] > 0 else 30,
            "format": "MJPG",
            "auto_exposure": True,
            "buffer_size": 3
        }
        
        if config["default_camera"] is None:
            config["default_camera"] = camera_id
    
    return config

if __name__ == "__main__":
    print("VisiFruit USB Camera Detection")
    print("=" * 50)
    
    cameras = find_usb_cameras()
    
    if not cameras:
        print("✗ No USB cameras found")
        sys.exit(1)
    
    print(f"✓ Found {len(cameras)} USB camera(s):")
    for camera in cameras:
        print(f"  {camera['device']}: {camera['width']}x{camera['height']} @ {camera['fps']}fps")
    
    # Create configuration
    config = create_camera_config(cameras)
    
    config_path = "/home/visifruit/VisiFruit/config/detected_cameras.json"
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\n✓ Configuration saved to {config_path}")
    sys.exit(0)
EOF
    
    chmod +x "$VISIFRUIT_DIR/test_csi_camera.py"
    chmod +x "$VISIFRUIT_DIR/test_usb_cameras.py"
    chown "$VISIFRUIT_USER:$VISIFRUIT_USER" "$VISIFRUIT_DIR/test_csi_camera.py"
    chown "$VISIFRUIT_USER:$VISIFRUIT_USER" "$VISIFRUIT_DIR/test_usb_cameras.py"
    
    log "SUCCESS" "Scripts de prueba creados"
}

# Create camera management script
create_camera_manager() {
    log "INFO" "Creando script de gestión de cámaras..."
    
    cat > /usr/local/bin/visifruit-camera << 'EOF'
#!/bin/bash

# VisiFruit Camera Management Script

VISIFRUIT_DIR="/home/visifruit/VisiFruit"

case "$1" in
    detect)
        echo "Detectando cámaras disponibles..."
        python3 "$VISIFRUIT_DIR/test_usb_cameras.py"
        python3 "$VISIFRUIT_DIR/test_csi_camera.py"
        ;;
    test)
        camera_id=${2:-0}
        echo "Probando cámara $camera_id..."
        python3 -c "
import cv2
cap = cv2.VideoCapture($camera_id)
if cap.isOpened():
    ret, frame = cap.read()
    if ret:
        print('✓ Cámara $camera_id funcionando')
        print(f'  Resolución: {frame.shape[1]}x{frame.shape[0]}')
    else:
        print('✗ No se puede capturar de cámara $camera_id')
    cap.release()
else:
    print('✗ No se puede abrir cámara $camera_id')
"
        ;;
    info)
        echo "Información de cámaras del sistema:"
        echo "=================================="
        
        # CSI camera info
        if command -v libcamera-hello &>/dev/null; then
            echo "CSI Cameras (libcamera):"
            libcamera-hello --list-cameras 2>/dev/null || echo "  No CSI cameras detected"
        fi
        
        echo ""
        echo "USB Cameras (V4L2):"
        if ls /dev/video* &>/dev/null; then
            for device in /dev/video*; do
                if [[ -c "$device" ]]; then
                    info=$(v4l2-ctl --device="$device" --info 2>/dev/null | grep "Card type" | cut -d: -f2 | xargs)
                    echo "  $device: $info"
                fi
            done
        else
            echo "  No USB cameras detected"
        fi
        
        echo ""
        echo "GPU Memory: $(vcgencmd get_mem gpu)"
        echo "Temperature: $(vcgencmd measure_temp)"
        ;;
    *)
        echo "Uso: $0 {detect|test [camera_id]|info}"
        exit 1
        ;;
esac
EOF
    
    chmod +x /usr/local/bin/visifruit-camera
    
    log "SUCCESS" "Script de gestión creado"
}

# Main execution
main() {
    print_header
    
    if [[ $EUID -ne 0 ]]; then
        log "ERROR" "Este script debe ejecutarse como root (sudo)"
        exit 1
    fi
    
    if [[ ! -d "$VISIFRUIT_DIR" ]]; then
        log "ERROR" "Directorio VisiFruit no encontrado: $VISIFRUIT_DIR"
        log "ERROR" "Ejecute primero el instalador principal"
        exit 1
    fi
    
    echo "Configuración de cámaras para VisiFruit"
    echo ""
    
    read -p "¿Continuar? (y/N): " -r
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
    
    # Main configuration steps
    log "INFO" "Iniciando configuración de cámaras..."
    
    detect_cameras
    create_camera_tests
    create_camera_manager
    
    echo ""
    log "SUCCESS" "Configuración de cámaras completada"
    echo ""
    echo -e "${CYAN}Comandos disponibles:${NC}"
    echo -e "  • ${YELLOW}visifruit-camera detect${NC}      - Detectar cámaras"
    echo -e "  • ${YELLOW}visifruit-camera test [id]${NC}   - Probar cámara"
    echo -e "  • ${YELLOW}visifruit-camera info${NC}        - Info del sistema"
    echo ""
}

# Execute main function
main "$@"
