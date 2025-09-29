# 🚀 Guía Rápida: Modos de Operación VisiFruit v4.0

## 🎯 ¿Qué Modo Usar?

VisiFruit v4.0 ahora tiene **DOS MODOS DE OPERACIÓN** para adaptarse a diferentes necesidades:

---

## 🎨 MODO PROTOTIPO

### ¿Para Qué?
- ✅ Pruebas y desarrollo
- ✅ Educación y demostraciones
- ✅ Producción de bajo volumen (20-30 frutas/min)
- ✅ Presupuesto limitado
- ✅ Aprender el sistema

### Hardware Necesario
```
✓ Raspberry Pi 4/5
✓ 1 Motor stepper + Driver DRV8825
✓ 3 Servomotores MG995
✓ Cámara USB o Pi Camera
✓ Banda transportadora simple
✓ Fuente de alimentación 5V 3A
```

### Costo Aproximado
**$150 - $300 USD**

### Inicio Rápido

#### 1. Configurar Variable de Entorno
```bash
# Establecer modo prototipo
export VISIFRUIT_MODE=prototype

# O editar archivo .env
echo "VISIFRUIT_MODE=prototype" >> .env
```

#### 2. Verificar Configuración
```bash
# Debe existir este archivo
ls Prototipo_Clasificador/Config_Prototipo.json
```

#### 3. Ejecutar Sistema
```bash
# Ejecutar directamente
python3 main_etiquetadora_v4.py

# O ejecutar prototipo standalone
python3 Prototipo_Clasificador/smart_classifier_system.py
```

#### 4. Verificar Funcionamiento
Deberías ver:
```
🎯 MODO PROTOTIPO - Sistema de Clasificación con IA
=====================================================
   - 1 Etiquetadora DRV8825
   - 3 Servomotores MG995 (Clasificación)
   - IA RT-DETR para detección
```

### Configuración de Pines (Config_Prototipo.json)

```json
{
  "labeler_settings": {
    "step_pin_bcm": 19,
    "dir_pin_bcm": 26,
    "enable_pin_bcm": 21
  },
  "servo_settings": {
    "apple": {"pin_bcm": 17},
    "pear": {"pin_bcm": 27},
    "lemon": {"pin_bcm": 22}
  },
  "belt_settings": {
    "relay1_pin": 22,
    "relay2_pin": 23
  }
}
```

### Ventajas
- ✅ Bajo costo
- ✅ Fácil de montar
- ✅ Perfecto para aprender
- ✅ Totalmente funcional
- ✅ Código abierto completo

### Limitaciones
- ⚠️ Velocidad limitada (~25 frutas/min)
- ⚠️ Una sola etiquetadora
- ⚠️ Clasificación simple con servos

---

## 🏭 MODO PROFESIONAL

### ¿Para Qué?
- ✅ Producción industrial (100+ frutas/min)
- ✅ Alta capacidad y velocidad
- ✅ Múltiples líneas simultáneas
- ✅ Operación 24/7
- ✅ Máxima precisión

### Hardware Necesario
```
✓ Raspberry Pi 5 (recomendado)
✓ 6 Motores stepper + Drivers DRV8825
✓ Motor DC lineal con driver L298N/BTS7960
✓ Sistema de desviadores industriales
✓ Cámara industrial de alta velocidad
✓ Banda transportadora profesional
✓ Fuente de alimentación industrial
✓ Sistema neumático (opcional)
```

### Costo Aproximado
**$1,500 - $3,000 USD**

### Inicio Rápido

#### 1. Configurar Variable de Entorno
```bash
# Establecer modo profesional (o dejarlo en auto)
export VISIFRUIT_MODE=professional

# O editar archivo .env
echo "VISIFRUIT_MODE=professional" >> .env
```

#### 2. Verificar Configuración
```bash
# Debe existir este archivo
ls Config_Etiquetadora.json
```

#### 3. Ejecutar Sistema Completo
```bash
# Con frontend y backend automáticos
python3 main_etiquetadora_v4.py
```

#### 4. Verificar Funcionamiento
Deberías ver:
```
🏭 MODO PROFESIONAL - Sistema Industrial Completo
==================================================
   - 6 Etiquetadoras Automáticas (2 por categoría)
   - Motor DC Lineal para posicionamiento
   - Sistema de desviadores industriales
   - IA RT-DETR avanzada

🌐 URLs del Sistema:
   🏷️ Sistema Principal: http://localhost:8000
   📊 Dashboard Backend: http://localhost:8001
   🎨 Interfaz Frontend: http://localhost:3000
```

### Arquitectura
```
Manzanas: Etiquetadoras 0 y 1
Peras:    Etiquetadoras 2 y 3
Limones:  Etiquetadoras 4 y 5

Motor DC Lineal → Posiciona grupo activo
Desviadores → Clasifican a cajas finales
```

### Ventajas
- ✅ Alta velocidad (100+ frutas/min)
- ✅ Redundancia (2 etiquetadoras por categoría)
- ✅ Posicionamiento automático
- ✅ Dashboard web completo
- ✅ Sistema de métricas avanzado
- ✅ Base de datos integrada
- ✅ API REST completa

### Requisitos
- ⚠️ Inversión mayor
- ⚠️ Montaje más complejo
- ⚠️ Mantenimiento especializado

---

## 🔄 Auto-Detección de Modo

El sistema puede detectar automáticamente el modo:

```bash
# Dejarlo en modo auto (por defecto)
export VISIFRUIT_MODE=auto
```

**Criterio de detección:**
1. Si existe `Prototipo_Clasificador/Config_Prototipo.json` y NO existe `Config_Etiquetadora.json` → **PROTOTIPO**
2. En cualquier otro caso → **PROFESIONAL**

---

## 📊 Comparación Rápida

| Característica | Prototipo | Profesional |
|----------------|-----------|-------------|
| **Costo** | $150-300 | $1,500-3,000 |
| **Etiquetadoras** | 1 | 6 |
| **Velocidad** | 20-30/min | 100+/min |
| **Clasificación** | Servos MG995 | Desviadores industriales |
| **Complejidad** | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Dashboard Web** | ❌ | ✅ |
| **Base de Datos** | ❌ | ✅ |
| **API REST** | ❌ | ✅ |
| **Redundancia** | ❌ | ✅ |
| **Ideal para** | Educación, demos | Producción industrial |

---

## 🎓 ¿Cuál Elegir?

### Elige PROTOTIPO si:
- 👨‍🎓 Eres estudiante o estás aprendiendo
- 🧪 Quieres hacer pruebas de concepto
- 💰 Tienes presupuesto limitado
- 🏠 Producción casera o pequeña
- ⏱️ No necesitas alta velocidad

### Elige PROFESIONAL si:
- 🏭 Producción industrial seria
- 💼 Negocio establecido
- 📈 Necesitas alto volumen
- 💰 Tienes presupuesto para inversión
- 🔧 Tienes soporte técnico

---

## 🚀 Migración: De Prototipo a Profesional

¿Empezaste con prototipo y quieres escalar?

### Paso 1: Mantener Configuración Prototipo
```bash
# Guardar respaldo
cp -r Prototipo_Clasificador Prototipo_Clasificador.backup
```

### Paso 2: Crear Configuración Profesional
```bash
# Copiar plantilla
cp Config_Etiquetadora.json.example Config_Etiquetadora.json

# Editar según tu hardware
nano Config_Etiquetadora.json
```

### Paso 3: Cambiar Modo
```bash
# Cambiar variable de entorno
export VISIFRUIT_MODE=professional

# O eliminar variable para auto-detección
unset VISIFRUIT_MODE
```

### Paso 4: Instalar Hardware Adicional
```bash
# Seguir guía de instalación profesional
cat Guias\ de\ uso/README_V4.md
```

---

## 🛠️ Comandos Útiles

### Ver Modo Actual
```bash
# Ver variable de entorno
echo $VISIFRUIT_MODE

# Auto-detectar sin ejecutar
python3 -c "
import os
from pathlib import Path
mode = os.getenv('VISIFRUIT_MODE', 'auto')
if mode == 'auto':
    proto = Path('Prototipo_Clasificador/Config_Prototipo.json').exists()
    prof = Path('Config_Etiquetadora.json').exists()
    mode = 'prototype' if proto and not prof else 'professional'
print(f'Modo: {mode}')
"
```

### Cambiar Modo Temporalmente
```bash
# Solo para esta ejecución
VISIFRUIT_MODE=prototype python3 main_etiquetadora_v4.py

# O para toda la sesión
export VISIFRUIT_MODE=prototype
python3 main_etiquetadora_v4.py
```

### Ver Logs del Modo Activo
```bash
# Prototipo
tail -f logs/prototipo_clasificador.log

# Profesional
tail -f logs/backend_ultra.log
```

---

## 📖 Documentación Detallada

### Para Modo Prototipo:
- 📄 `Prototipo_Clasificador/README_PROTOTIPO.md`
- 📄 `IA_Etiquetado/README_IA_MEJORADA.md`

### Para Modo Profesional:
- 📄 `Guias de uso/README_V4.md`
- 📄 `Guias de uso/ARCHITECTURE_V4.md`

---

## 🆘 Solución de Problemas

### El sistema no detecta el modo correcto
```bash
# Verificar archivos de configuración
ls -la Config_Etiquetadora.json
ls -la Prototipo_Clasificador/Config_Prototipo.json

# Forzar modo específico
export VISIFRUIT_MODE=prototype  # o professional
```

### Error al cambiar de modo
```bash
# Limpiar procesos anteriores
pkill -f main_etiquetadora
pkill -f smart_classifier

# Reiniciar
python3 main_etiquetadora_v4.py
```

### Hardware no responde en prototipo
```bash
# Verificar GPIO
python3 -c "from utils.gpio_wrapper import get_gpio_info; print(get_gpio_info())"

# Verificar pigpio
sudo systemctl status pigpiod
```

---

## 🎯 Próximos Pasos

### Si Elegiste Prototipo:
1. ✅ Leer `Prototipo_Clasificador/README_PROTOTIPO.md`
2. ✅ Configurar pines en `Config_Prototipo.json`
3. ✅ Calibrar servos y DRV8825
4. ✅ Ajustar temporización según tu banda
5. ✅ Probar con frutas reales

### Si Elegiste Profesional:
1. ✅ Leer `Guias de uso/README_V4.md`
2. ✅ Instalar todo el hardware
3. ✅ Configurar `Config_Etiquetadora.json`
4. ✅ Probar cada componente individualmente
5. ✅ Iniciar producción completa

---

## 💡 Consejo Final

> **¡Empieza con PROTOTIPO!**
> 
> Incluso si planeas usar el modo profesional, es altamente recomendable comenzar con el prototipo para:
> - Entender el flujo del sistema
> - Probar la IA y ajustar modelos
> - Familiarizarte con el código
> - Hacer pruebas sin riesgo
> - Luego escalar a profesional con confianza

---

**¡Sistema listo para clasificar frutas de manera inteligente! 🍎🍐🍋**

Para más ayuda: consulta los archivos README de cada carpeta.
