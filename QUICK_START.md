# 🚀 Inicio Rápido - VisiFruit v2.0 Optimizado

## ⚡ TL;DR - Pasos Rápidos

### En el Servidor (Laptop/PC con GPU):
```bash
# 1. Instalar dependencias
pip install -r requirements_server.txt

# 2. Configurar IP fija: 192.168.1.50 (ver guía abajo)
# 3. Abrir puerto 9000 en firewall

# 4. Iniciar servidor
start_server.bat              # Windows
python ai_inference_server.py # Linux/Mac
```

### En la Raspberry Pi 5:
```bash
# 1. Instalar dependencias
pip install -r requirements_pi5.txt

# 2. Configurar IP fija: 192.168.1.100
# 3. Actualizar server_url en Config_Prototipo.json

# 4. Probar conexión
python test_connection.py

# 5. Iniciar clasificador
chmod +x start_classifier.sh
./start_classifier.sh
```

---

## 📋 Configuración Paso a Paso

### PASO 1: Preparar el Servidor (Windows)

#### 1.1 Instalar Dependencias
```powershell
# Crear entorno virtual
python -m venv venv
venv\Scripts\activate

# Instalar paquetes
pip install -r requirements_server.txt

# Si tienes GPU NVIDIA
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

#### 1.2 Configurar IP Fija
```powershell
# PowerShell como Administrador
New-NetIPAddress -InterfaceAlias "Wi-Fi" -IPAddress 192.168.1.50 -PrefixLength 24 -DefaultGateway 192.168.1.1
Set-DnsClientServerAddress -InterfaceAlias "Wi-Fi" -ServerAddresses 8.8.8.8,8.8.4.4
```

**O manualmente:** Panel de Control → Red → Propiedades TCP/IPv4

#### 1.3 Abrir Puerto en Firewall
```powershell
# PowerShell como Administrador
New-NetFirewallRule -DisplayName "VisiFruit AI Server" `
  -Direction Inbound -Protocol TCP -LocalPort 9000 `
  -Action Allow -Profile Private,Public
```

**O manualmente:** Windows Defender Firewall → Reglas de entrada → Nueva regla

#### 1.4 Iniciar Servidor
```bash
# Doble click o desde cmd:
start_server.bat
```

**Salida esperada:**
```
========================================
   VisiFruit AI Inference Server
========================================
🔄 Cargando modelo YOLOv8 desde weights/best.pt
🎮 GPU detectada: NVIDIA GeForce RTX 3060
🔥 Realizando warmup del modelo...
   Warmup 1/3: 45.2ms
   Warmup 2/3: 23.1ms
   Warmup 3/3: 22.8ms
✅ Modelo YOLOv8 cargado y listo

INFO: Uvicorn running on http://0.0.0.0:9000
```

### PASO 2: Preparar la Raspberry Pi 5

#### 2.1 Instalar Dependencias
```bash
# SSH a la Raspberry Pi
ssh pi@raspberrypi.local

cd ~/VisiFruit

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar paquetes
pip install -r requirements_pi5.txt
```

#### 2.2 Configurar IP Fija
```bash
# Editar configuración de red
sudo nano /etc/dhcpcd.conf

# Agregar al final:
interface wlan0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=8.8.8.8 8.8.4.4

# Guardar (Ctrl+O) y salir (Ctrl+X)

# Reiniciar red
sudo systemctl restart dhcpcd

# Verificar
ip addr show wlan0
```

#### 2.3 Actualizar Configuración
```bash
nano Prototipo_Clasificador/Config_Prototipo.json
```

**Verificar estos campos:**
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

#### 2.4 Probar Conexión
```bash
python test_connection.py
```

**Salida esperada:**
```
============================================================
  VisiFruit - Prueba de Conexión
============================================================
✓ httpx instalado

============================================================
  PRUEBA DE RED
============================================================
✓ Ping exitoso

============================================================
  PRUEBA DE CLIENTE ASÍNCRONO
============================================================
✓ Cliente asíncrono creado
✓ Health check exitoso (45.2ms)
✓ Inferencia exitosa (234.5ms)
✓ Benchmark completado:
   Promedio: 189.3ms
   Mínimo: 145.2ms
   Máximo: 287.1ms
✓ Rendimiento EXCELENTE (<300ms)

============================================================
  RESULTADO FINAL
============================================================
✓ TODAS LAS PRUEBAS EXITOSAS ✓
```

#### 2.5 Iniciar Clasificador
```bash
# Dar permisos de ejecución
chmod +x start_classifier.sh

# Iniciar sistema
./start_classifier.sh
```

**Salida esperada:**
```
========================================
   VisiFruit Smart Classifier
   Raspberry Pi 5 Edition
========================================
[+] Activando entorno virtual...
[+] Verificando dependencias criticas...
[+] Probando conectividad con servidor...
    ✓ Servidor alcanzable
    ✓ Health check exitoso
[+] Camara detectada en /dev/video0
[+] Iniciando clasificador inteligente...

=== 🚀 Inicializando Sistema Inteligente de Clasificación ===
📷 Inicializando cámara...
✅ Cámara inicializada correctamente.
🤖 Inicializando detector YOLOv8...
✅ Modo REMOTO habilitado y saludable (HTTP/2 async)
   🚀 Inferencia ultra-rápida con cliente asíncrono
...
=== ✅ Sistema inicializado correctamente ===
```

---

## 🔍 Verificación de Funcionamiento

### En el Servidor:
```bash
# Ver logs en tiempo real
# (El servidor muestra logs en la consola)

# Verificar health desde navegador
http://192.168.1.50:9000/health

# Ver estadísticas
http://192.168.1.50:9000/stats
```

### En la Raspberry Pi:
```bash
# Ver logs del sistema
tail -f logs/prototipo_clasificador.log

# Ver estadísticas en tiempo real (desde otro terminal)
watch -n 1 'curl -s http://localhost:8000/api/system/status | python3 -m json.tool'
```

---

## 📊 Métricas Esperadas

### Rendimiento Normal:
- **Latencia de inferencia:** 150-400ms
- **FPS con detección:** 2-3 FPS
- **FPS sin detección:** 25-30 FPS
- **Tasa de éxito:** >95%
- **Circuit breaker:** Estado "closed"

### Si ves estos valores, ¡todo funciona perfecto! ✅

---

## ❌ Solución Rápida de Problemas

### "Connection refused"
```bash
# En servidor: Verificar que está corriendo
netstat -an | grep 9000  # Linux
netstat -an | findstr 9000  # Windows

# Si no aparece, reiniciar servidor
```

### "Authentication failed"
```bash
# Verificar que los tokens coinciden

# En servidor (archivo .env o variables):
AUTH_TOKENS=visifruittoken2025

# En Pi (Config_Prototipo.json):
"auth_token": "visifruittoken2025"
```

### "Circuit Breaker OPEN"
```bash
# Significa que el servidor está caído o no responde
# Reiniciar el servidor y esperar ~20 segundos
```

### Latencia muy alta (>1s)
```json
// Reducir calidad en Config_Prototipo.json
{
  "remote_inference": {
    "jpeg_quality": 70,
    "max_dimension": 480
  },
  "ai_model_settings": {
    "input_size": 480
  }
}
```

---

## 🎯 Checklist Pre-Inicio

Antes de iniciar el sistema completo:

### Servidor:
- [ ] Python 3.8+ instalado
- [ ] Dependencias instaladas (`requirements_server.txt`)
- [ ] Modelo `weights/best.pt` existe
- [ ] IP fija configurada (192.168.1.50)
- [ ] Puerto 9000 abierto en firewall
- [ ] GPU configurada (opcional)

### Raspberry Pi:
- [ ] Python 3.8+ instalado
- [ ] Dependencias instaladas (`requirements_pi5.txt`)
- [ ] IP fija configurada (192.168.1.100)
- [ ] Config_Prototipo.json actualizado
- [ ] Conexión al servidor verificada (test_connection.py)
- [ ] Cámara conectada
- [ ] GPIO configurados (ver RASPBERRY_PI5_PWM_SETUP.md)

---

## 📚 Documentación Adicional

| Documento | Descripción |
|-----------|-------------|
| `PERFORMANCE_UPGRADE.md` | Detalles técnicos de las mejoras |
| `NETWORK_SETUP_GUIDE.md` | Guía completa de configuración de red |
| `RASPBERRY_PI5_PWM_SETUP.md` | Configuración de PWM para servos |
| `test_connection.py` | Script de prueba de conexión |

---

## 🎉 ¡Listo!

Si completaste todos los pasos, tu sistema debería estar funcionando **3-4x más rápido** que antes.

### Características Nuevas:
✅ Cliente HTTP/2 asíncrono ultra-rápido  
✅ Circuit breaker inteligente  
✅ Compresión adaptativa de imágenes  
✅ Autenticación por tokens  
✅ Rate limiting  
✅ Cache de resultados  
✅ Recuperación automática de errores  

### Mejoras de Rendimiento:
- **Antes:** 800-1500ms por inferencia
- **Ahora:** 150-400ms por inferencia
- **Ganancia:** 70-80% más rápido ⚡

---

## 📞 ¿Necesitas Ayuda?

1. Ejecuta `python test_connection.py` para diagnóstico
2. Revisa los logs en `logs/`
3. Consulta NETWORK_SETUP_GUIDE.md
4. Verifica que todas las IPs y puertos coincidan

---

**¡Tu sistema de clasificación inteligente está listo para producción!** 🚀🍎🍐🍋
