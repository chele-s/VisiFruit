#!/bin/bash
# quick_start_ov5647.sh
# Script de inicio rápido para sistema optimizado OV5647 + YOLOv8

set -e

echo "=========================================="
echo "🚀 VisiFruit - Inicio Rápido OV5647"
echo "=========================================="
echo ""

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Verificar que estamos en el directorio correcto
if [ ! -f "main_etiquetadora_v4.py" ]; then
    echo -e "${RED}❌ Error: Ejecuta este script desde el directorio VisiFruit${NC}"
    exit 1
fi

# Activar entorno virtual
echo -e "${YELLOW}📦 Activando entorno virtual...${NC}"
if [ -d "venv" ]; then
    source venv/bin/activate
    echo -e "${GREEN}✓ Entorno virtual activado${NC}"
else
    echo -e "${RED}❌ No se encontró venv. Ejecuta: python -m venv venv${NC}"
    exit 1
fi

# Verificar dependencias críticas
echo ""
echo -e "${YELLOW}🔍 Verificando dependencias...${NC}"

# Verificar Picamera2
if python -c "from picamera2 import Picamera2" 2>/dev/null; then
    echo -e "${GREEN}✓ Picamera2 disponible${NC}"
else
    echo -e "${YELLOW}⚠️  Picamera2 no encontrada en venv${NC}"
    echo "   Instalando desde sistema..."
    sudo apt install -y python3-picamera2 python3-libcamera 2>/dev/null || true
    cp -r /usr/lib/python3/dist-packages/picamera2 venv/lib/python3.11/site-packages/ 2>/dev/null || true
    cp -r /usr/lib/python3/dist-packages/libcamera venv/lib/python3.11/site-packages/ 2>/dev/null || true
fi

# Verificar YOLOv8
if python -c "from ultralytics import YOLO" 2>/dev/null; then
    echo -e "${GREEN}✓ YOLOv8 (Ultralytics) disponible${NC}"
else
    echo -e "${RED}❌ YOLOv8 no instalado${NC}"
    echo "   Instala con: pip install ultralytics"
    exit 1
fi

# Verificar modelo
echo ""
if [ -f "weights/best.pt" ]; then
    echo -e "${GREEN}✓ Modelo YOLOv8 encontrado (weights/best.pt)${NC}"
else
    echo -e "${RED}❌ Modelo YOLOv8 no encontrado${NC}"
    echo "   Por favor, descarga tu modelo entrenado de Roboflow"
    echo "   y guárdalo en: weights/best.pt"
    exit 1
fi

# Test de cámara
echo ""
echo -e "${YELLOW}📷 Probando cámara OV5647...${NC}"
if rpicam-hello --list-cameras 2>/dev/null | grep -q "ov5647"; then
    echo -e "${GREEN}✓ Cámara OV5647 detectada${NC}"
else
    echo -e "${YELLOW}⚠️  No se pudo verificar la cámara${NC}"
    echo "   Asegúrate de que la cámara CSI está conectada"
fi

# Menú de opciones
echo ""
echo "=========================================="
echo "¿Qué deseas hacer?"
echo "=========================================="
echo ""
echo "  [1] 🧪 Test rápido de cámara + IA (10 frames)"
echo "  [2] 📊 Benchmark completo (100 frames)"
echo "  [3] 🚀 Iniciar sistema completo (Modo PROTOTIPO)"
echo "  [4] 📄 Ver guía de optimización"
echo "  [5] 🚪 Salir"
echo ""

read -p "👉 Selecciona una opción (1-5): " option

case $option in
    1)
        echo ""
        echo -e "${GREEN}🧪 Ejecutando test rápido...${NC}"
        python test_camera_ai_optimized.py --quick
        ;;
    2)
        echo ""
        echo -e "${GREEN}📊 Ejecutando benchmark completo...${NC}"
        python test_camera_ai_optimized.py --full
        ;;
    3)
        echo ""
        echo -e "${GREEN}🚀 Iniciando sistema completo...${NC}"
        echo ""
        python main_etiquetadora_v4.py
        ;;
    4)
        echo ""
        if [ -f "OPTIMIZACION_OV5647.md" ]; then
            cat OPTIMIZACION_OV5647.md | less
        else
            echo -e "${RED}❌ Guía no encontrada${NC}"
        fi
        ;;
    5)
        echo ""
        echo "👋 ¡Hasta luego!"
        exit 0
        ;;
    *)
        echo ""
        echo -e "${RED}❌ Opción inválida${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}✅ Proceso completado${NC}"
echo ""
