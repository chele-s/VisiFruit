# 🌐 Guía Completa de Configuración de Red - VisiFruit

## 📋 Tabla de Contenidos
1. [Configuración del Servidor (Laptop/PC)](#configuración-del-servidor-laptoppc)
2. [Configuración del Cliente (Raspberry Pi 5)](#configuración-del-cliente-raspberry-pi-5)
3. [Instalación de Dependencias](#instalación-de-dependencias)
4. [Configuración de Seguridad](#configuración-de-seguridad)
5. [Pruebas y Verificación](#pruebas-y-verificación)
6. [Solución de Problemas](#solución-de-problemas)
7. [Optimización de Rendimiento](#optimización-de-rendimiento)

---

## 🖥️ Configuración del Servidor (Laptop/PC)

### 1. Asignar IP Fija en Windows

#### Método 1: Por Interfaz Gráfica
1. Abre **Panel de Control** → **Centro de redes y recursos compartidos**
2. Click en **Cambiar configuración del adaptador**
3. Click derecho en tu conexión WiFi/Ethernet → **Propiedades**
4. Selecciona **Protocolo de Internet versión 4 (TCP/IPv4)** → **Propiedades**
5. Selecciona **Usar la siguiente dirección IP:**
   ```
   Dirección IP:        192.168.1.50
   Máscara de subred:   255.255.255.0
   Puerta de enlace:    192.168.1.1
   DNS preferido:       8.8.8.8
   DNS alternativo:     8.8.4.4
   ```

#### Método 2: Por PowerShell (Administrador)
```powershell
# Ver interfaces de red
Get-NetAdapter

# Configurar IP fija (reemplaza "Wi-Fi" con tu interfaz)
New-NetIPAddress -InterfaceAlias "Wi-Fi" -IPAddress 192.168.1.50 -PrefixLength 24 -DefaultGateway 192.168.1.1

# Configurar DNS
Set-DnsClientServerAddress -InterfaceAlias "Wi-Fi" -ServerAddresses 8.8.8.8, 8.8.4.4

# Verificar configuración
ipconfig /all
```

### 2. Configurar Firewall de Windows

#### Método 1: Por PowerShell (Recomendado)
```powershell
# Abrir PowerShell como Administrador

# Crear regla de entrada para el puerto 9000 (servidor IA)
New-NetFirewallRule -DisplayName "VisiFruit AI Server" `
  -Direction Inbound -Protocol TCP -LocalPort 9000 `
  -Action Allow -Profile Private,Public

# Verificar que la regla fue creada
Get-NetFirewallRule -DisplayName "VisiFruit AI Server"

# (Opcional) Crear regla solo para IP de la Raspberry Pi
New-NetFirewallRule -DisplayName "VisiFruit AI Server - Pi Only" `
  -Direction Inbound -Protocol TCP -LocalPort 9000 `
  -Action Allow -RemoteAddress 192.168.1.100/32 `
  -Profile Private
```

#### Método 2: Por Interfaz Gráfica
1. Abre **Windows Defender Firewall con seguridad avanzada**
2. Click en **Reglas de entrada** → **Nueva regla...**
3. Tipo de regla: **Puerto**
4. Protocolo: **TCP**, Puerto específico: **9000**
5. Acción: **Permitir la conexión**
6. Perfiles: ✅ Privado, ✅ Público
7. Nombre: **VisiFruit AI Server**

### 3. Iniciar el Servidor de IA

#### Crear archivo .env para configuración
```bash
# archivo: .env (en el directorio de VisiFruit)
MODEL_PATH=weights/best.pt
MODEL_DEVICE=cuda
MODEL_FP16=true
AUTH_ENABLED=true
AUTH_TOKENS=visifruittoken2025,debugtoken
SERVER_HOST=0.0.0.0
SERVER_PORT=9000
RATE_LIMIT=60/minute
```

#### Script de inicio (Windows)
```batch
@echo off
REM archivo: start_server.bat
echo ========================================
echo   VisiFruit AI Server - Iniciando...
echo ========================================
echo.

REM Activar entorno virtual si existe
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Configurar CUDA si está disponible
set CUDA_VISIBLE_DEVICES=0

REM Iniciar servidor
python ai_inference_server.py

pause
```

---

## 🍓 Configuración del Cliente (Raspberry Pi 5)

### 1. Asignar IP Fija en Raspberry Pi

#### Método 1: Archivo dhcpcd.conf (Recomendado)
```bash
# Editar configuración de red
sudo nano /etc/dhcpcd.conf

# Agregar al final del archivo:
interface wlan0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=8.8.8.8 8.8.4.4

# Si usas Ethernet en lugar de WiFi:
interface eth0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=8.8.8.8 8.8.4.4

# Reiniciar servicio
sudo systemctl restart dhcpcd

# Verificar IP
ip addr show
```

#### Método 2: NetworkManager (Raspberry Pi OS reciente)
```bash
# Ver conexiones
nmcli connection show

# Configurar IP fija (reemplaza "preconfigured" con tu conexión)
sudo nmcli connection modify preconfigured ipv4.method manual \
  ipv4.addresses 192.168.1.100/24 \
  ipv4.gateway 192.168.1.1 \
  ipv4.dns "8.8.8.8 8.8.4.4"

# Reiniciar conexión
sudo nmcli connection down preconfigured
sudo nmcli connection up preconfigured
```

### 2. Configurar Cliente en Raspberry Pi

#### Actualizar Config_Prototipo.json
```json
{
  "remote_inference": {
    "enabled": true,
    "server_url": "http://192.168.1.50:9000",
    "auth_token": "visifruittoken2025",
    ...
  }
}
```

---

## 📦 Instalación de Dependencias

### En el Servidor (Laptop/PC)

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno (Windows)
venv\Scripts\activate

# Activar entorno (Linux/Mac)
source venv/bin/activate

# Instalar dependencias del servidor
pip install fastapi uvicorn ultralytics
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
pip install opencv-python numpy pillow
pip install psutil gputil
pip install slowapi python-multipart

# Para mejor rendimiento
pip install httpx[http2]
```

### En el Cliente (Raspberry Pi 5)

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias del sistema
sudo apt install -y python3-pip python3-venv python3-dev
sudo apt install -y libopencv-dev python3-opencv
sudo apt install -y libatlas-base-dev libopenblas-dev

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar cliente asíncrono
pip install httpx[http2]
pip install numpy opencv-python-headless

# (Opcional) Si necesitas fallback local
pip install ultralytics --no-deps
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

---

## 🔐 Configuración de Seguridad

### 1. Generar Token Seguro

```python
# Script para generar token seguro
import secrets
import hashlib

# Generar token aleatorio
token = secrets.token_hex(32)
print(f"Token generado: {token}")

# O basado en una frase
passphrase = "VisiFruit2025SecureToken"
token = hashlib.sha256(passphrase.encode()).hexdigest()
print(f"Token desde frase: {token}")
```

### 2. Configurar HTTPS (Opcional pero Recomendado)

#### Generar certificado autofirmado
```bash
# En el servidor
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Modificar ai_inference_server.py para usar HTTPS
uvicorn.run(
    app,
    host=SERVER_HOST,
    port=SERVER_PORT,
    ssl_keyfile="key.pem",
    ssl_certfile="cert.pem"
)
```

#### Actualizar cliente para HTTPS
```json
{
  "remote_inference": {
    "server_url": "https://192.168.1.50:9000",
    ...
  }
}
```

---

## 🧪 Pruebas y Verificación

### 1. Probar Conectividad

```bash
# Desde Raspberry Pi, hacer ping al servidor
ping 192.168.1.50

# Verificar que el puerto está abierto
nc -zv 192.168.1.50 9000

# O con nmap
nmap -p 9000 192.168.1.50
```

### 2. Probar Health Check

```bash
# Desde Raspberry Pi (sin token para health)
curl http://192.168.1.50:9000/health

# Con httpie (más legible)
http GET 192.168.1.50:9000/health
```

### 3. Probar Inferencia

```python
# test_inference.py
import httpx
import asyncio
import cv2
import json

async def test_inference():
    # Configuración
    server_url = "http://192.168.1.50:9000"
    token = "visifruittoken2025"
    
    # Cargar imagen de prueba
    image = cv2.imread("test_apple.jpg")
    _, buffer = cv2.imencode('.jpg', image)
    
    # Cliente HTTP/2
    async with httpx.AsyncClient(http2=True) as client:
        # Health check
        health = await client.get(f"{server_url}/health")
        print(f"Health: {health.json()}")
        
        # Inferencia
        files = {"image": ("test.jpg", buffer.tobytes(), "image/jpeg")}
        headers = {"Authorization": f"Bearer {token}"}
        data = {"conf": 0.5, "imgsz": 640}
        
        response = await client.post(
            f"{server_url}/infer",
            files=files,
            data=data,
            headers=headers
        )
        
        result = response.json()
        print(f"Detecciones: {len(result['detections'])}")
        print(f"Tiempo total: {result['total_ms']:.1f}ms")
        
        for det in result['detections']:
            print(f"  - {det['class_name']}: {det['confidence']:.2f}")

# Ejecutar test
asyncio.run(test_inference())
```

---

## 🔧 Solución de Problemas

### Problema 1: Conexión Rechazada
```bash
# Verificar que el servidor está corriendo
netstat -an | grep 9000

# En Windows
netstat -an | findstr 9000

# Verificar firewall
# Windows: Desactivar temporalmente para probar
netsh advfirewall set allprofiles state off
# IMPORTANTE: Reactivar después
netsh advfirewall set allprofiles state on
```

### Problema 2: Timeout en Inferencia
```python
# Aumentar timeouts en Config_Prototipo.json
{
  "remote_inference": {
    "connect_timeout_s": 1.0,  # Aumentar
    "read_timeout_s": 3.0,      # Aumentar
    ...
  }
}
```

### Problema 3: Token Inválido
```bash
# Verificar token en servidor
echo %AUTH_TOKENS%  # Windows
echo $AUTH_TOKENS    # Linux

# Verificar token en cliente
grep auth_token Config_Prototipo.json
```

### Problema 4: Lentitud en Red WiFi
```bash
# Optimizar WiFi en Raspberry Pi
sudo iwconfig wlan0 power off  # Desactivar ahorro de energía

# Usar banda 5GHz si está disponible
sudo nano /etc/wpa_supplicant/wpa_supplicant.conf
# Agregar freq_list=5180 5200 5220 5240 5260 5280
```

---

## ⚡ Optimización de Rendimiento

### 1. Optimización del Servidor

```python
# Variables de entorno para mejor rendimiento
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4
export CUDA_LAUNCH_BLOCKING=0

# Usar workers múltiples (solo si tienes suficiente RAM)
uvicorn ai_inference_server:app --workers 2
```

### 2. Optimización del Cliente

```python
# En Config_Prototipo.json
{
  "remote_inference": {
    "jpeg_quality": 75,      # Reducir para menos datos
    "max_dimension": 480,    # Reducir resolución
    "auto_quality": true,    # Ajuste automático
    ...
  },
  "ai_model_settings": {
    "input_size": 480,       # Menor = más rápido
    ...
  }
}
```

### 3. Monitoreo de Rendimiento

```bash
# En el servidor - Monitor de GPU
nvidia-smi -l 1

# En el servidor - Monitor de red
iftop -i eth0

# En Raspberry Pi - Monitor de sistema
htop

# En Raspberry Pi - Monitor de red
sudo tcpdump -i wlan0 port 9000
```

### 4. Benchmark de Latencia

```python
# benchmark.py
import time
import asyncio
from IA_Etiquetado.async_inference_client import AsyncInferenceClient
import numpy as np

async def benchmark():
    config = {
        "server_url": "http://192.168.1.50:9000",
        "auth_token": "visifruittoken2025"
    }
    
    client = AsyncInferenceClient(config)
    
    # Imagen dummy
    frame = np.random.randint(0, 255, (640, 480, 3), dtype=np.uint8)
    
    # Warmup
    await client.health()
    
    # Benchmark
    times = []
    for i in range(10):
        start = time.time()
        result = await client.infer(frame)
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
        print(f"Iteración {i+1}: {elapsed:.1f}ms")
    
    avg = sum(times) / len(times)
    print(f"\nLatencia promedio: {avg:.1f}ms")
    print(f"Min: {min(times):.1f}ms, Max: {max(times):.1f}ms")
    
    await client.close()

asyncio.run(benchmark())
```

---

## 📊 Métricas de Rendimiento Esperadas

### Con Configuración Optimizada:
- **Latencia de red**: < 5ms (LAN cableada), < 20ms (WiFi 5GHz)
- **Compresión de imagen**: ~50-100ms
- **Inferencia en servidor (GPU)**: ~20-50ms
- **Inferencia en servidor (CPU)**: ~100-300ms
- **Total end-to-end**: ~150-400ms

### Comparación:
- **Antes (requests síncrono)**: 800-1500ms
- **Después (httpx asíncrono)**: 150-400ms
- **Mejora**: 70-80% más rápido

---

## 🎯 Checklist de Configuración

- [ ] IP fija configurada en servidor (192.168.1.50)
- [ ] IP fija configurada en Raspberry Pi (192.168.1.100)
- [ ] Puerto 9000 abierto en firewall de Windows
- [ ] Token de autenticación configurado en ambos lados
- [ ] Servidor IA iniciado y verificado con health check
- [ ] Cliente asíncrono instalado en Raspberry Pi
- [ ] Config_Prototipo.json actualizado con nueva configuración
- [ ] Prueba de inferencia exitosa
- [ ] Circuit breaker configurado y probado
- [ ] Logs verificados sin errores

---

## 📞 Soporte

Si encuentras problemas:
1. Revisa los logs del servidor: `logs/ai_server.log`
2. Revisa los logs del cliente: `logs/prototipo_clasificador.log`
3. Verifica conectividad de red con ping y netstat
4. Asegúrate de que las IPs y puertos coincidan
5. Verifica que los tokens sean idénticos

¡Con esta configuración tu sistema debería funcionar hasta 80% más rápido! 🚀
