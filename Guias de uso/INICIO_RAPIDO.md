# 🚀 VisiFruit v4.0 - Inicio Rápido

## ⚡ Empezar en 5 Minutos

### Opción 1: Script Automático (Más Fácil)

```bash
# 1. Hacer script ejecutable (solo primera vez)
chmod +x start_visifruit.sh

# 2. Ejecutar (auto-detecta el modo)
./start_visifruit.sh
```

### Opción 2: Python Directo

```bash
# Ejecutar con auto-detección de modo
python3 main_etiquetadora_v4.py
```

---

## 🎯 Elegir Tu Modo

### 🎨 MODO PROTOTIPO
**¿Para ti si...?**
- Estás aprendiendo el sistema
- Tienes presupuesto limitado ($150-300)
- Quieres hacer pruebas rápidas
- No necesitas alta velocidad

**Hardware:**
- 1 Stepper DRV8825
- 3 Servos MG995
- Raspberry Pi 4/5
- Cámara USB

**Iniciar:**
```bash
VISIFRUIT_MODE=prototype python3 main_etiquetadora_v4.py
```

### 🏭 MODO PROFESIONAL
**¿Para ti si...?**
- Producción industrial seria
- Alto volumen (100+ frutas/min)
- Presupuesto profesional ($1,500-3,000)
- Necesitas redundancia

**Hardware:**
- 6 Steppers DRV8825
- Motor DC lineal
- Desviadores industriales
- Raspberry Pi 5
- Cámara industrial

**Iniciar:**
```bash
VISIFRUIT_MODE=professional python3 main_etiquetadora_v4.py
```

---

## 📋 Primeros Pasos

### 1. Verificar Modo
```bash
# Ver qué modo se detectará
./start_visifruit.sh help
```

### 2. Configurar Hardware

**Prototipo:**
```bash
# Editar configuración
nano Prototipo_Clasificador/Config_Prototipo.json

# Ajustar pines GPIO:
# - Servos: BCM 17, 27, 22
# - DRV8825: BCM 19, 26, 21
# - Banda: BCM 22, 23, 27
```

**Profesional:**
```bash
# Editar configuración
nano Config_Etiquetadora.json
```

### 3. Probar Componentes

**Probar Servos (Prototipo):**
```bash
python3 Prototipo_Clasificador/mg995_servo_controller.py
```

**Probar Sistema Completo (Prototipo):**
```bash
python3 Prototipo_Clasificador/smart_classifier_system.py
```

---

## 🧠 Sistema de IA Mejorado

**Nueva precisión: >95%** (antes ~85%)

El sistema ahora usa **validación temporal**:
- Requiere 2-5 detecciones para confirmar
- Calcula consenso entre frames
- Detecta calidad de frutas
- Aprende continuamente

**No necesitas hacer nada especial**, la IA mejorada se activa automáticamente.

---

## 📊 Ver Estadísticas

Mientras el sistema está corriendo:

```bash
# Ver logs en tiempo real
tail -f logs/prototipo_clasificador.log

# O para modo profesional
tail -f logs/backend_ultra.log
```

El sistema muestra cada 10-30 segundos:
```
📊 Detectadas: 150 | Etiquetadas: 148 | Clasificadas: 145
```

---

## 🛑 Detener Sistema

```bash
# Presionar Ctrl+C en la terminal
# El sistema hará limpieza automática y detendrá todo ordenadamente
```

---

## 🆘 Problemas Comunes

### "Error: GPIO no disponible"
```bash
# En Windows/desarrollo → OK, usa modo simulación
# En Raspberry → Verificar permisos:
sudo usermod -a -G gpio $USER
sudo chmod 666 /dev/gpiomem
```

### "Modelo de IA no encontrado"
```bash
# Verificar que existe el modelo
ls -lh IA_Etiquetado/Dataset_Frutas/best.pt

# Si no existe, entrenar o copiar modelo
```

### "Servos no responden"
```bash
# 1. Verificar alimentación (4.8-7.2V, 2A+ por servo)
# 2. Verificar pigpiod
sudo systemctl status pigpiod
sudo systemctl start pigpiod
```

### "IA detecta mal / muchos falsos positivos"
```bash
# Ajustar en Config_Prototipo.json:
"ai_settings": {
  "confidence_threshold": 0.7  // Subir para ser más estricto
}
```

---

## 📚 Documentación Completa

| Documento | Contenido |
|-----------|-----------|
| `GUIA_RAPIDA_MODOS.md` | Comparación detallada de modos |
| `Prototipo_Clasificador/README_PROTOTIPO.md` | Guía completa prototipo |
| `IA_Etiquetado/README_IA_MEJORADA.md` | Sistema IA mejorado |
| `Guias de uso/README_V4.md` | Guía completa profesional |
| `RESUMEN_CAMBIOS_V4.md` | Todos los cambios v4.0 |

---

## 🎓 Flujo Básico del Sistema

```
1. 📷 Cámara captura fruta en banda
         ↓
2. 🧠 IA detecta clase (manzana/pera/limón)
   └─ Valida con 2-5 frames para confirmar
         ↓
3. 🏷️ DRV8825 etiqueta la fruta
         ↓
4. ⏱️ Sistema calcula delay automático
         ↓
5. 🔄 Servo MG995 activa compuerta
         ↓
6. 📦 Fruta cae en caja correcta
```

---

## 🎯 Calibración Rápida

### Temporización (Crítico!)

```bash
# 1. Medir distancia cámara → clasificador
#    Ejemplo: 50cm = 0.5m

# 2. Medir velocidad de banda
#    Marcar fruta, cronometrar 1 metro
#    Ejemplo: 1m en 5s = 0.2 m/s

# 3. Actualizar en Config_Prototipo.json:
"timing": {
  "belt_speed_mps": 0.2,  # TU VELOCIDAD
  "camera_to_classifier_distance_m": 0.5  # TU DISTANCIA
}
```

El sistema calcula automáticamente:
```
Delay = Distancia / Velocidad = 0.5m / 0.2m/s = 2.5 segundos
```

---

## 💡 Consejos Profesionales

### 1. Empieza Simple
```bash
# Primero probar cada componente por separado
# Luego integrar todo
```

### 2. Usa Modo Simulación en Desarrollo
```bash
# En Windows/Mac → Funciona en simulación
# Perfecto para desarrollar sin hardware
```

### 3. Ajusta IA Gradualmente
```bash
# Empezar con umbral bajo (0.5)
# Ir subiendo conforme mejora precisión
```

### 4. Logs son Tus Amigos
```bash
# Siempre revisar logs para debug
tail -f logs/*.log
```

---

## ✅ Checklist Primer Uso

- [ ] Hardware conectado y alimentado
- [ ] Configuración editada (pines, velocidades)
- [ ] Modelo de IA disponible
- [ ] Cámara funcionando
- [ ] GPIO accesible (en Raspberry)
- [ ] Sistema iniciado correctamente
- [ ] Primera detección exitosa
- [ ] Servo activado correctamente
- [ ] Sincronización temporal OK

---

## 🎉 ¡Listo!

Una vez completado el checklist, tu sistema está **listo para clasificar frutas inteligentemente!**

**¿Dudas?** Consulta la documentación completa en las guías mencionadas.

**¿Problemas?** Revisa logs y sección de solución de problemas en los READMEs.

---

**¡A clasificar frutas! 🍎🍐🍋**
