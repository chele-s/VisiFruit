#!/bin/bash
# =====================================================================
# VisiFruit - Sistema de Etiquetado Industrial
# Launcher Interactivo con Selector de Modo
# =====================================================================

echo ""
echo "========================================================================="
echo "  _    ___     _______       _ __     ___     ____ _______"
echo " | |  / (_)___/_  __(_)___  (_) /_   / / /   / __ \`/ ___/"
echo " | | / / / ___// / / / __ \/ / __/  / / /   / /_/ / __ \ "
echo " | |/ / (__  )/ / / / /_/ / / /_   /_/_/   \__,_/____/"
echo " |___/_/____//_/ /_/\____/_/\__/  (_|_)"
echo ""
echo "        Sistema de Etiquetado Industrial v4.0"
echo "========================================================================="
echo ""

# Activar entorno virtual si existe
if [ -f "venv/bin/activate" ]; then
    echo "[+] Activando entorno virtual..."
    source venv/bin/activate
else
    echo "[!] ADVERTENCIA: No se encontró entorno virtual"
    echo "[!] Ejecutando con Python del sistema..."
fi

echo ""
echo "[+] Iniciando VisiFruit..."
echo ""

# Ejecutar sistema
python3 main_etiquetadora_v4.py

echo ""
echo "========================================================================="
echo "Sistema finalizado"
echo "========================================================================="
echo ""

