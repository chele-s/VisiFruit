#!/bin/bash
# start_visifruit.sh
# Script de inicio rápido para VisiFruit v4.0
# Auto-detecta modo y ejecuta sistema apropiado

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Banner
echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════════╗"
echo "║                                                   ║"
echo "║         🍎 VisiFruit v4.0 - Launcher 🍋          ║"
echo "║     Sistema Inteligente de Clasificación         ║"
echo "║                                                   ║"
echo "╚═══════════════════════════════════════════════════╝"
echo -e "${NC}"

# Función para detectar modo
detect_mode() {
    # Verificar variable de entorno
    if [ ! -z "$VISIFRUIT_MODE" ] && [ "$VISIFRUIT_MODE" != "auto" ]; then
        echo "$VISIFRUIT_MODE"
        return
    fi
    
    # Auto-detectar basándose en archivos de configuración
    if [ -f "Prototipo_Clasificador/Config_Prototipo.json" ] && [ ! -f "Config_Etiquetadora.json" ]; then
        echo "prototype"
    else
        echo "professional"
    fi
}

# Función para mostrar ayuda
show_help() {
    echo -e "${YELLOW}Uso:${NC}"
    echo "  ./start_visifruit.sh [MODO]"
    echo ""
    echo -e "${YELLOW}Modos disponibles:${NC}"
    echo "  prototype    - Ejecutar modo prototipo (1 etiquetadora + servos MG995)"
    echo "  professional - Ejecutar modo profesional (6 etiquetadoras + motor DC)"
    echo "  auto         - Auto-detectar modo (por defecto)"
    echo "  help         - Mostrar esta ayuda"
    echo ""
    echo -e "${YELLOW}Ejemplos:${NC}"
    echo "  ./start_visifruit.sh                 # Auto-detectar"
    echo "  ./start_visifruit.sh prototype       # Forzar prototipo"
    echo "  ./start_visifruit.sh professional    # Forzar profesional"
    echo ""
    echo -e "${YELLOW}Variables de entorno:${NC}"
    echo "  VISIFRUIT_MODE=prototype|professional|auto"
    echo "  AUTO_START_FRONTEND=true|false"
    echo "  AUTO_START_BACKEND=true|false"
    echo ""
}

# Función para verificar dependencias
check_dependencies() {
    echo -e "${BLUE}🔍 Verificando dependencias...${NC}"
    
    # Python 3
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 no encontrado${NC}"
        return 1
    fi
    echo -e "${GREEN}✓${NC} Python 3: $(python3 --version)"
    
    # Verificar módulos Python críticos
    python3 -c "import numpy, cv2, torch" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}⚠️ Algunos módulos Python no están instalados${NC}"
        echo "   Ejecuta: pip3 install -r requirements.txt"
    else
        echo -e "${GREEN}✓${NC} Módulos Python OK"
    fi
    
    return 0
}

# Función para verificar hardware GPIO
check_gpio() {
    if [ -e "/dev/gpiomem" ]; then
        echo -e "${GREEN}✓${NC} GPIO disponible"
        return 0
    else
        echo -e "${YELLOW}⚠️ GPIO no detectado - Modo simulación activo${NC}"
        return 1
    fi
}

# Función para iniciar modo prototipo
start_prototype() {
    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════╗"
    echo "║     🎯 MODO PROTOTIPO - Clasificador IA          ║"
    echo "╚═══════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    # Verificar configuración
    if [ ! -f "Prototipo_Clasificador/Config_Prototipo.json" ]; then
        echo -e "${RED}❌ Archivo de configuración no encontrado:${NC}"
        echo "   Prototipo_Clasificador/Config_Prototipo.json"
        echo ""
        echo "   Copia la plantilla de ejemplo o consulta la documentación:"
        echo "   cat Prototipo_Clasificador/README_PROTOTIPO.md"
        exit 1
    fi
    
    echo -e "${BLUE}📋 Hardware:${NC}"
    echo "   • 1 Etiquetadora DRV8825"
    echo "   • 3 Servomotores MG995"
    echo "   • IA RT-DETR para detección"
    echo ""
    
    # Verificar GPIO
    check_gpio
    
    echo -e "${GREEN}🚀 Iniciando sistema prototipo...${NC}"
    echo ""
    
    # Establecer variable de entorno
    export VISIFRUIT_MODE=prototype
    
    # Ejecutar
    python3 main_etiquetadora_v4.py
}

# Función para iniciar modo profesional
start_professional() {
    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════╗"
    echo "║  🏭 MODO PROFESIONAL - Sistema Industrial        ║"
    echo "╚═══════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    # Verificar configuración
    if [ ! -f "Config_Etiquetadora.json" ]; then
        echo -e "${RED}❌ Archivo de configuración no encontrado:${NC}"
        echo "   Config_Etiquetadora.json"
        echo ""
        echo "   Consulta la documentación:"
        echo "   cat Guias\ de\ uso/README_V4.md"
        exit 1
    fi
    
    echo -e "${BLUE}📋 Hardware:${NC}"
    echo "   • 6 Etiquetadoras Automáticas"
    echo "   • Motor DC Lineal"
    echo "   • Sistema de desviadores"
    echo "   • IA RT-DETR avanzada"
    echo ""
    
    # Verificar servicios opcionales
    echo -e "${BLUE}🌐 Servicios web:${NC}"
    
    AUTO_FRONTEND=${AUTO_START_FRONTEND:-true}
    AUTO_BACKEND=${AUTO_START_BACKEND:-true}
    
    if [ "$AUTO_FRONTEND" = "true" ]; then
        echo "   • Frontend React: http://localhost:3000"
    fi
    
    if [ "$AUTO_BACKEND" = "true" ]; then
        echo "   • Backend Dashboard: http://localhost:8001"
    fi
    
    echo "   • Sistema Principal: http://localhost:8000"
    echo ""
    
    # Verificar GPIO
    check_gpio
    
    echo -e "${GREEN}🚀 Iniciando sistema profesional completo...${NC}"
    echo ""
    
    # Establecer variable de entorno
    export VISIFRUIT_MODE=professional
    
    # Ejecutar
    python3 main_etiquetadora_v4.py
}

# ==================== MAIN ====================

# Cambiar al directorio del script
cd "$(dirname "$0")"

# Verificar argumentos
MODE="${1:-auto}"

case "$MODE" in
    help|-h|--help)
        show_help
        exit 0
        ;;
    
    prototype|prototipo)
        check_dependencies || exit 1
        start_prototype
        ;;
    
    professional|profesional)
        check_dependencies || exit 1
        start_professional
        ;;
    
    auto)
        check_dependencies || exit 1
        DETECTED_MODE=$(detect_mode)
        
        echo -e "${CYAN}🔍 Auto-detección de modo...${NC}"
        echo ""
        
        if [ "$DETECTED_MODE" = "prototype" ]; then
            echo -e "${GREEN}✓${NC} Modo detectado: ${CYAN}PROTOTIPO${NC}"
            echo ""
            start_prototype
        else
            echo -e "${GREEN}✓${NC} Modo detectado: ${CYAN}PROFESIONAL${NC}"
            echo ""
            start_professional
        fi
        ;;
    
    *)
        echo -e "${RED}❌ Modo no reconocido: $MODE${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
