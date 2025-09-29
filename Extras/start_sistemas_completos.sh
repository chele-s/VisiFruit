#!/bin/bash
# ============================================================================
# Script de Inicio Completo - VisiFruit
# ============================================================================
# Inicia todos los sistemas necesarios para el control de banda:
# - Sistema Principal (puerto 8000)
# - Sistema Demo (puerto 8002)
# - Backend UI (puerto 8001)
# - Frontend React (puerto 5173)
# ============================================================================

set -e  # Exit on error

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo ""
echo "========================================================================"
echo "  🚀 VisiFruit - Inicio de Sistemas Completos"
echo "========================================================================"
echo ""

# Cambiar al directorio del proyecto
cd "$(dirname "$0")/.."

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ ERROR: Python3 no está instalado${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python3 encontrado${NC}"
echo ""

# Crear directorio de logs si no existe
mkdir -p logs

echo "📋 Selecciona qué sistemas deseas iniciar:"
echo ""
echo "[1] Sistema Principal (puerto 8000) - Versión profesional"
echo "[2] Sistema Demo (puerto 8002) - Versión prototipo/demo"
echo "[3] Ambos sistemas"
echo "[4] Todo (Sistemas + Backend UI + Frontend)"
echo ""

read -p "Tu elección (1-4): " choice

start_main() {
    echo ""
    echo -e "${BLUE}🎯 Iniciando Sistema Principal...${NC}"
    echo ""
    gnome-terminal --title="VisiFruit - Sistema Principal (8000)" -- bash -c "python3 main_etiquetadora_v4.py; exec bash" &
    sleep 2
    echo -e "${GREEN}✅ Sistema Principal iniciado en http://localhost:8000${NC}"
}

start_demo() {
    echo ""
    echo -e "${BLUE}🎮 Iniciando Sistema Demo...${NC}"
    echo ""
    gnome-terminal --title="VisiFruit - Sistema Demo (8002)" -- bash -c "python3 Control_Etiquetado/demo_sistema_web_server.py; exec bash" &
    sleep 2
    echo -e "${GREEN}✅ Sistema Demo iniciado en http://localhost:8002${NC}"
}

start_backend_ui() {
    echo ""
    echo -e "${BLUE}🔧 Iniciando Backend UI...${NC}"
    echo ""
    cd Interfaz_Usuario/Backend
    gnome-terminal --title="VisiFruit - Backend UI (8001)" -- bash -c "python3 main.py; exec bash" &
    cd ../..
    sleep 2
    echo -e "${GREEN}✅ Backend UI iniciado en http://localhost:8001${NC}"
}

start_frontend() {
    echo ""
    echo -e "${BLUE}🌐 Iniciando Frontend React...${NC}"
    echo ""
    cd Interfaz_Usuario/VisiFruit
    if [ -d "node_modules" ]; then
        gnome-terminal --title="VisiFruit - Frontend (5173)" -- bash -c "npm run dev; exec bash" &
    else
        echo -e "${YELLOW}⚠️  Advertencia: node_modules no encontrado${NC}"
        echo "   Ejecuta 'npm install' primero en Interfaz_Usuario/VisiFruit"
    fi
    cd ../..
    sleep 2
    echo -e "${GREEN}✅ Frontend iniciado en http://localhost:5173${NC}"
}

case $choice in
    1)
        start_main
        ;;
    2)
        start_demo
        ;;
    3)
        echo ""
        echo -e "${BLUE}🔄 Iniciando ambos sistemas...${NC}"
        echo ""
        start_main
        sleep 1
        start_demo
        echo ""
        echo -e "${GREEN}✅ Ambos sistemas iniciados:${NC}"
        echo "   - Principal: http://localhost:8000"
        echo "   - Demo: http://localhost:8002"
        ;;
    4)
        echo ""
        echo -e "${BLUE}🚀 Iniciando TODOS los servicios...${NC}"
        echo ""
        
        echo "[1/4] Iniciando Sistema Principal..."
        start_main
        sleep 1
        
        echo "[2/4] Iniciando Sistema Demo..."
        start_demo
        sleep 1
        
        echo "[3/4] Iniciando Backend UI..."
        start_backend_ui
        sleep 1
        
        echo "[4/4] Iniciando Frontend React..."
        start_frontend
        
        echo ""
        echo -e "${GREEN}✅ Todos los servicios iniciados:${NC}"
        echo "   - Sistema Principal: http://localhost:8000"
        echo "   - Sistema Demo: http://localhost:8002"
        echo "   - Backend UI: http://localhost:8001"
        echo "   - Frontend: http://localhost:5173"
        echo ""
        echo -e "${BLUE}💡 Abre tu navegador en: http://localhost:5173${NC}"
        ;;
    *)
        echo ""
        echo -e "${RED}❌ Opción inválida. Por favor elige 1, 2, 3 o 4.${NC}"
        exit 1
        ;;
esac

echo ""
echo "========================================================================"
echo "  ✅ Sistemas iniciados correctamente"
echo "========================================================================"
echo ""
echo "📖 Para probar la integración, ejecuta:"
echo "   python3 Extras/test_belt_integration.py"
echo ""
echo "🌐 Accede a la interfaz web:"
echo "   http://localhost:5173"
echo ""
echo "📚 Documentación:"
echo "   Guias de uso/INTEGRACION_FRONTEND_BANDA.md"
echo ""
