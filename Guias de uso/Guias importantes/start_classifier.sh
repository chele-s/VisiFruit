#!/bin/bash
# ========================================
#   VisiFruit Smart Classifier
#   Cliente optimizado para Raspberry Pi 5
# ========================================

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================"
echo "   VisiFruit Smart Classifier"
echo "   Raspberry Pi 5 Edition"
echo -e "========================================${NC}"
echo

# Verificar que estamos en el directorio correcto
if [ ! -f "Prototipo_Clasificador/smart_classifier_system.py" ]; then
    echo -e "${RED}ERROR: No se encuentra smart_classifier_system.py${NC}"
    echo "Asegurate de ejecutar este script desde el directorio VisiFruit"
    exit 1
fi

# Activar entorno virtual si existe
if [ -f "venv/bin/activate" ]; then
    echo -e "${GREEN}[+] Activando entorno virtual...${NC}"
    source venv/bin/activate
else
    echo -e "${YELLOW}[!] No se encontro entorno virtual. Usando Python del sistema...${NC}"
fi

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: Python3 no esta instalado${NC}"
    exit 1
fi

# Verificar dependencias críticas
echo -e "${GREEN}[+] Verificando dependencias criticas...${NC}"

python3 -c "import httpx" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: httpx no esta instalado${NC}"
    echo "Instala con: pip install httpx[http2]"
    exit 1
fi

python3 -c "import cv2" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}[!] ADVERTENCIA: OpenCV no esta instalado${NC}"
fi

python3 -c "import gpiozero" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}[!] ADVERTENCIA: gpiozero no esta instalado${NC}"
fi

# Verificar configuración
CONFIG_FILE="Prototipo_Clasificador/Config_Prototipo.json"
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}ERROR: No se encuentra $CONFIG_FILE${NC}"
    exit 1
fi

# Extraer configuración del servidor remoto
SERVER_URL=$(python3 -c "import json; f=open('$CONFIG_FILE'); c=json.load(f); print(c.get('remote_inference', {}).get('server_url', 'N/A'))")
REMOTE_ENABLED=$(python3 -c "import json; f=open('$CONFIG_FILE'); c=json.load(f); print(c.get('remote_inference', {}).get('enabled', False))")

echo
echo -e "${BLUE}========================================"
echo "   CONFIGURACION"
echo -e "========================================${NC}"
echo -e "   Modo remoto:   ${GREEN}$REMOTE_ENABLED${NC}"
echo -e "   Servidor:      ${GREEN}$SERVER_URL${NC}"
echo -e "   Config:        ${GREEN}$CONFIG_FILE${NC}"
echo -e "${BLUE}========================================${NC}"
echo

# Probar conectividad con servidor si está habilitado
if [ "$REMOTE_ENABLED" == "True" ]; then
    echo -e "${GREEN}[+] Probando conectividad con servidor...${NC}"
    
    # Extraer host del URL
    SERVER_HOST=$(echo $SERVER_URL | sed -e 's|^[^/]*//||' -e 's|:.*||')
    
    if ping -c 1 -W 2 $SERVER_HOST &> /dev/null; then
        echo -e "${GREEN}    ✓ Servidor alcanzable${NC}"
        
        # Intentar health check
        if command -v curl &> /dev/null; then
            HEALTH_URL="$SERVER_URL/health"
            if curl -s -m 2 "$HEALTH_URL" &> /dev/null; then
                echo -e "${GREEN}    ✓ Health check exitoso${NC}"
            else
                echo -e "${YELLOW}    ! Health check fallido (servidor puede no estar iniciado)${NC}"
            fi
        fi
    else
        echo -e "${YELLOW}    ! No se puede alcanzar el servidor${NC}"
        echo -e "${YELLOW}    El sistema usara fallback local si esta configurado${NC}"
    fi
    echo
fi

# Verificar permisos GPIO (solo en Raspberry Pi)
if [ -e "/dev/gpiomem" ]; then
    if [ ! -r "/dev/gpiomem" ] || [ ! -w "/dev/gpiomem" ]; then
        echo -e "${YELLOW}[!] ADVERTENCIA: Sin permisos GPIO. Algunos componentes pueden fallar.${NC}"
        echo "    Agrega tu usuario al grupo gpio: sudo usermod -a -G gpio $USER"
        echo
    fi
fi

# Verificar camara
if [ -e "/dev/video0" ]; then
    echo -e "${GREEN}[+] Camara detectada en /dev/video0${NC}"
else
    echo -e "${YELLOW}[!] No se detecto camara. Sistema funcionara sin captura de video.${NC}"
fi

echo
echo -e "${GREEN}[+] Iniciando clasificador inteligente...${NC}"
echo -e "${YELLOW}    Presiona Ctrl+C para detener${NC}"
echo

# Cambiar al directorio del prototipo
cd Prototipo_Clasificador

# Iniciar el sistema
python3 smart_classifier_system.py

# Si el sistema se detiene
EXIT_CODE=$?
echo
echo -e "${BLUE}========================================"
echo "   Sistema detenido (codigo: $EXIT_CODE)"
echo -e "========================================${NC}"

# Volver al directorio original
cd ..

exit $EXIT_CODE
