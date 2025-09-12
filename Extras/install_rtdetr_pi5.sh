#!/bin/bash

# ========================================================================
# VisiFruit v3.0 - Instalador Específico RT-DETR para Raspberry Pi 5
# Configuración optimizada de RT-DETR y dependencias IA
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
VENV_PATH="$VISIFRUIT_DIR/venv"
LOG_FILE="/tmp/rtdetr_install.log"

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
    echo "              🤖 VisiFruit RT-DETR Installer for Pi 5"
    echo "                 Real-Time Detection Transformer"
    echo "════════════════════════════════════════════════════════════════"
    echo -e "${NC}\n"
}

# Check prerequisites
check_prerequisites() {
    log "STEP" "Verificando prerequisitos..."
    
    if [[ $EUID -ne 0 ]]; then
        log "ERROR" "Este script debe ejecutarse como root (sudo)"
        exit 1
    fi
    
    if [[ ! -d "$VISIFRUIT_DIR" ]]; then
        log "ERROR" "Directorio VisiFruit no encontrado: $VISIFRUIT_DIR"
        log "ERROR" "Ejecute primero el instalador principal"
        exit 1
    fi
    
    # Check Python virtual environment
    if [[ ! -d "$VENV_PATH" ]]; then
        log "ERROR" "Entorno virtual Python no encontrado"
        log "ERROR" "Ejecute primero el instalador principal"
        exit 1
    fi
    
    log "SUCCESS" "Prerequisitos verificados"
}

# Install PyTorch optimized for Pi 5
install_pytorch() {
    log "STEP" "Instalando PyTorch optimizado para Raspberry Pi 5..."
    
    # Update pip first
    sudo -u "$VISIFRUIT_USER" "$VENV_PATH/bin/pip" install --upgrade pip setuptools wheel
    
    # Install PyTorch with ARM64 optimizations
    log "INFO" "Instalando PyTorch para ARM64..."
    sudo -u "$VISIFRUIT_USER" "$VENV_PATH/bin/pip" install \
        torch==2.1.0 \
        torchvision==0.16.0 \
        torchaudio==2.1.0 \
        --index-url https://download.pytorch.org/whl/cpu
    
    # Verify PyTorch installation
    if sudo -u "$VISIFRUIT_USER" "$VENV_PATH/bin/python" -c "import torch; print(f'PyTorch {torch.__version__} installed successfully')"; then
        log "SUCCESS" "PyTorch instalado correctamente"
    else
        log "ERROR" "Fallo en la instalación de PyTorch"
        return 1
    fi
    
    log "SUCCESS" "PyTorch y dependencias instaladas"
}

# Install Transformers and HuggingFace libraries
install_transformers() {
    log "STEP" "Instalando Transformers y librerías HuggingFace..."
    
    # Install core transformers
    sudo -u "$VISIFRUIT_USER" "$VENV_PATH/bin/pip" install \
        transformers==4.35.2 \
        accelerate==0.24.1 \
        datasets==2.14.6 \
        tokenizers==0.15.0
    
    # Install additional ML libraries
    log "INFO" "Instalando librerías adicionales de ML..."
    sudo -u "$VISIFRUIT_USER" "$VENV_PATH/bin/pip" install \
        scikit-learn==1.3.2 \
        scipy==1.11.4 \
        pandas==2.1.4 \
        numpy==1.24.4
    
    log "SUCCESS" "Transformers y dependencias instaladas"
}

# Install YOLO as fallback
install_yolo_fallback() {
    log "STEP" "Instalando YOLO como fallback..."
    
    sudo -u "$VISIFRUIT_USER" "$VENV_PATH/bin/pip" install \
        ultralytics==8.0.221
    
    log "SUCCESS" "YOLO fallback instalado"
}

# Configure RT-DETR environment
configure_rtdetr_environment() {
    log "STEP" "Configurando entorno RT-DETR..."
    
    # Create RT-DETR configuration directory
    sudo -u "$VISIFRUIT_USER" mkdir -p "$VISIFRUIT_DIR/config/rtdetr"
    
    # Create RT-DETR environment configuration
    cat > "$VISIFRUIT_DIR/config/rtdetr/environment.sh" << 'EOF'
#!/bin/bash
# RT-DETR Environment Configuration for Raspberry Pi 5

# PyTorch optimizations
export PYTORCH_CUDA_ALLOC_CONF="max_split_size_mb:512"
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4

# RT-DETR specific settings
export RT_DETR_BATCH_SIZE=1
export RT_DETR_NUM_WORKERS=2
export RT_DETR_PRECISION="fp16"
export RT_DETR_BACKEND="pytorch"

# OpenCV optimizations
export OPENCV_LOG_LEVEL="ERROR"
EOF
    
    chown "$VISIFRUIT_USER:$VISIFRUIT_USER" "$VISIFRUIT_DIR/config/rtdetr/environment.sh"
    chmod +x "$VISIFRUIT_DIR/config/rtdetr/environment.sh"
    
    log "SUCCESS" "Entorno RT-DETR configurado"
}

# Create RT-DETR test script
create_rtdetr_test() {
    log "STEP" "Creando script de prueba RT-DETR..."
    
    cat > "$VISIFRUIT_DIR/test_rtdetr.py" << 'EOF'
#!/usr/bin/env python3
"""
RT-DETR Test Script for Raspberry Pi 5
"""

import sys
import time
import numpy as np

def test_pytorch():
    """Test PyTorch installation"""
    print("Testing PyTorch...")
    try:
        import torch
        print(f"✅ PyTorch {torch.__version__} installed")
        print(f"   CPU threads: {torch.get_num_threads()}")
        return True
    except ImportError as e:
        print(f"❌ PyTorch not available: {e}")
        return False

def test_transformers():
    """Test Transformers library"""
    print("\nTesting Transformers...")
    try:
        import transformers
        print(f"✅ Transformers {transformers.__version__} installed")
        return True
    except ImportError as e:
        print(f"❌ Transformers not available: {e}")
        return False

def test_opencv():
    """Test OpenCV installation"""
    print("\nTesting OpenCV...")
    try:
        import cv2
        print(f"✅ OpenCV {cv2.__version__} installed")
        return True
    except ImportError as e:
        print(f"❌ OpenCV not available: {e}")
        return False

def main():
    """Run all tests"""
    print("="*60)
    print("        RT-DETR Installation Test - Raspberry Pi 5")
    print("="*60)
    
    tests = [
        ("PyTorch", test_pytorch),
        ("Transformers", test_transformers),
        ("OpenCV", test_opencv),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"❌ {name} test failed with exception: {e}")
            results[name] = False
        print()
    
    # Summary
    print("="*60)
    print("TEST SUMMARY:")
    print("="*60)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:<30} {status}")
    
    print(f"\nTotal: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n🎉 All tests passed! RT-DETR is ready for production.")
    else:
        print("\n❌ Some test failures. Please check installation.")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
EOF
    
    chmod +x "$VISIFRUIT_DIR/test_rtdetr.py"
    chown "$VISIFRUIT_USER:$VISIFRUIT_USER" "$VISIFRUIT_DIR/test_rtdetr.py"
    
    log "SUCCESS" "Script de prueba RT-DETR creado"
}

# Create RT-DETR management script
create_rtdetr_manager() {
    log "STEP" "Creando script de gestión RT-DETR..."
    
    cat > /usr/local/bin/visifruit-rtdetr << 'EOF'
#!/bin/bash

# VisiFruit RT-DETR Management Script

VISIFRUIT_DIR="/home/visifruit/VisiFruit"
VENV_PATH="$VISIFRUIT_DIR/venv"

case "$1" in
    test)
        echo "Ejecutando pruebas RT-DETR..."
        cd "$VISIFRUIT_DIR"
        sudo -u visifruit "$VENV_PATH/bin/python" test_rtdetr.py
        ;;
    info)
        echo "Información RT-DETR:"
        echo "===================="
        
        cd "$VISIFRUIT_DIR"
        
        # Check PyTorch
        echo "PyTorch:"
        sudo -u visifruit "$VENV_PATH/bin/python" -c "import torch; print(f'  Version: {torch.__version__}'); print(f'  Threads: {torch.get_num_threads()}')" 2>/dev/null || echo "  Not installed"
        
        # Check Transformers
        echo "Transformers:"
        sudo -u visifruit "$VENV_PATH/bin/python" -c "import transformers; print(f'  Version: {transformers.__version__}')" 2>/dev/null || echo "  Not installed"
        ;;
    *)
        echo "Uso: $0 {test|info}"
        echo ""
        echo "  test      - Ejecutar pruebas RT-DETR"
        echo "  info      - Mostrar información de instalación"
        exit 1
        ;;
esac
EOF
    
    chmod +x /usr/local/bin/visifruit-rtdetr
    
    log "SUCCESS" "Script de gestión RT-DETR creado"
}

# Main execution
main() {
    print_header
    
    log "INFO" "Instalador específico RT-DETR para Raspberry Pi 5"
    echo ""
    
    check_prerequisites
    
    read -p "¿Continuar con la instalación de RT-DETR? (y/N): " -r
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
    
    log "INFO" "Iniciando instalación RT-DETR..."
    echo ""
    
    # Installation steps
    install_pytorch
    install_transformers
    install_yolo_fallback
    configure_rtdetr_environment
    create_rtdetr_test
    create_rtdetr_manager
    
    echo ""
    log "SUCCESS" "Instalación RT-DETR completada"
    echo ""
    echo -e "${CYAN}Comandos RT-DETR disponibles:${NC}"
    echo -e "  • ${YELLOW}visifruit-rtdetr test${NC}      - Probar instalación RT-DETR"
    echo -e "  • ${YELLOW}visifruit-rtdetr info${NC}      - Información del sistema"
    echo ""
}

# Execute main function
main "$@"
