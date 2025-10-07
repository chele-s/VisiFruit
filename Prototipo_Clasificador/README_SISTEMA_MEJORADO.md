# 🎉 Sistema de Clasificación Mejorado - Prototipo VisiFruit

## ✨ Mejoras Implementadas

El sistema de clasificación con servos MG995 ha sido completamente mejorado para eliminar oscilaciones y comportamientos erráticos.

### 🔧 Problemas Solucionados

- ✅ **Servos "volviéndose locos"** - Eliminadas oscilaciones y movimientos erráticos
- ✅ **Control preciso de ángulos** - Sistema de hold rígido implementado
- ✅ **Retorno suave** - Movimiento interpolado sin sacudidas
- ✅ **Protección contra activaciones simultáneas** - Un servo a la vez

---

## 🚀 Inicio Rápido

### 1. Configuración de Ángulos

Los servos están configurados con los ángulos que solicitaste:

| Categoría | Movimiento | Ángulos |
|-----------|------------|---------|
| 🍎 **Manzanas** | -100° | 90° → 0° |
| 🍐 **Peras** | +90° | 90° → 180° |
| 🍋 **Limones** | -80° | 90° → 10° |

**Posición default (90°):** Pieza de madera en posición neutra  
**Activación:** Servo se mueve, se mantiene rígido 1.5s, y regresa suavemente

### 2. Ejecutar el Sistema

```bash
# Desde el directorio raíz del proyecto
python main_etiquetadora_v4.py
```

Selecciona **[2] MODO PROTOTIPO** cuando se te pregunte.

### 3. Probar Servos Individualmente

```bash
cd Prototipo_Clasificador
python test_servos_mg995.py
```

Este script te permite:
- ✅ Probar cada servo individualmente
- ✅ Ejecutar secuencia de todos los servos
- ✅ Calibrar ángulos manualmente
- ✅ Verificar protección contra activaciones rápidas

---

## 📐 Ajustes de Configuración

### Archivo: `Config_Prototipo.json`

#### Ángulos de los Servos

```json
{
  "servo_settings": {
    "apple": {
      "default_angle": 90,      // Posición de reposo
      "activation_angle": -10,  // -100° de movimiento (normalizado a 0°)
      "hold_duration_s": 1.5    // Tiempo rígido en posición
    }
  }
}
```

**Cómo ajustar:**

1. Ejecuta `test_servos_mg995.py`
2. Selecciona opción **[6] Modo de CALIBRACIÓN**
3. Mueve el servo a la posición deseada
4. Anota el ángulo
5. Actualiza `activation_angle` en el JSON

#### Timing del Sistema

```json
{
  "timing": {
    "classification_delay_s": 0.5,  // Delay antes de clasificar
    "min_servo_activation_interval_s": 2.0  // Intervalo mínimo
  }
}
```

**Recomendaciones:**

- `classification_delay_s`: Ajusta según distancia cámara → servo
- `min_servo_activation_interval_s`: Aumenta si hay errores de activación simultánea

---

## 🔍 Verificación del Sistema

### ¿Cómo saber si funciona correctamente?

Al clasificar una fruta, deberías observar:

1. **Detección de IA** 🤖
   ```
   ✨ ¡DETECCIÓN! 1 fruta(s) encontrada(s)
   🎯 APPLE detectada | Confianza: 85.3%
   ```

2. **Activación del DRV8825** (etiquetadora) 🏷️
   ```
   🏷️ Activando etiquetadora por 0.5s @ 30%
   ```

3. **Clasificación con Servo** (después de delay) 📦
   ```
   ============================================================
   📦 ¡CLASIFICANDO FRUTA!
      Tipo: APPLE 🍎
      Categoría: apple
   ============================================================
   🤖 Activando servo apple
      📐 90° → -10° (Δ -100°)
      ⏱️ Hold: 1.5s | Total: 2.0s
      🔒 Manteniendo posición rígida por 1.5s...
      🔄 Retornando suavemente a 90°...
   ✅ 🍎 APPLE clasificada exitosamente
   ============================================================
   ```

### Comportamiento Esperado del Servo

1. ⚡ **Movimiento rápido** a posición de activación (~0.3s)
2. 🔒 **Hold rígido** manteniendo posición (1.5s)
3. 🔄 **Retorno suave** a posición inicial (0.5s)
4. 🛑 **Parada completa** sin vibraciones ni oscilaciones

---

## 🐛 Solución de Problemas

### Problema: Servo oscila o vibra

**Síntomas:**
- Servo se mueve pero vibra en la posición
- Ruido continuo del servo

**Solución:**
1. Verifica que `hold_duration_s > 0` en la configuración
2. Comprueba la alimentación del servo (debe ser 6V estable)
3. Ejecuta el test: `python test_servos_mg995.py`

### Problema: Servo no se mueve

**Síntomas:**
- La IA detecta frutas
- No hay movimiento del servo

**Solución:**
1. Verifica conexiones GPIO:
   - Pin 5 (BCM) → Servo Manzanas
   - Pin 6 (BCM) → Servo Peras
   - Pin 7 (BCM) → Servo Limones
2. Comprueba alimentación de servos (6V)
3. Revisa logs: `logs/prototipo_clasificador.log`

### Problema: Múltiples servos activos simultáneamente

**Síntomas:**
- Varios servos se mueven al mismo tiempo
- Comportamiento errático

**Solución:**
1. Verifica que el sistema esté actualizado
2. Comprueba que `min_servo_activation_interval_s >= 0.5`
3. Reinicia el sistema

### Problema: Servo se mueve en dirección incorrecta

**Síntomas:**
- El movimiento es opuesto al esperado

**Solución:**
1. Ajusta `invert: true` en la configuración del servo
2. O bien, invierte los ángulos:
   ```json
   {
     "default_angle": 0,
     "activation_angle": 90
   }
   ```

---

## 📊 Monitoreo del Sistema

### Ver Estadísticas en Tiempo Real

El sistema muestra estadísticas cada 30 segundos:

```
📊 Detectadas: 15 | Etiquetadas: 15 | Clasificadas: 15
```

### Logs Detallados

Ubicación: `logs/prototipo_clasificador.log`

```bash
# Ver logs en tiempo real
tail -f logs/prototipo_clasificador.log

# Filtrar solo clasificaciones
grep "CLASIFICANDO" logs/prototipo_clasificador.log
```

---

## ⚙️ Parámetros Avanzados

### Ajuste Fino de Ángulos

Para cada servo, puedes ajustar:

```json
{
  "apple": {
    "default_angle": 90,          // Posición de reposo
    "activation_angle": -10,      // Posición al clasificar
    "hold_duration_s": 1.5,       // Tiempo en posición
    "activation_duration_s": 2.0, // Duración total
    "return_smoothly": true       // Retorno suave
  }
}
```

**Guía de ajuste:**

- `default_angle`: 
  - Ajusta para que la pieza de madera esté en posición neutra
  - Típicamente 90° (centro)

- `activation_angle`:
  - Ajusta para que la pieza empuje la fruta correctamente
  - Prueba con modo de calibración

- `hold_duration_s`:
  - Aumenta si la fruta no se clasifica completamente
  - Reduce para mayor velocidad (mínimo 1.0s)

- `return_smoothly`:
  - `true`: Retorno suave en 10 pasos (recomendado)
  - `false`: Retorno directo (más rápido pero brusco)

### Optimización de Velocidad

Para maximizar el throughput:

```json
{
  "timing": {
    "classification_delay_s": 0.3,  // Reducir si cámara está cerca
    "min_servo_activation_interval_s": 1.5  // Mínimo recomendado
  },
  "servo_settings": {
    "apple": {
      "hold_duration_s": 1.0  // Reducir si es posible
    }
  }
}
```

**Velocidad actual:** ~2.3s por clasificación  
**Velocidad optimizada:** ~1.8s por clasificación (con ajustes)

---

## 📈 Comparación Antes/Después

### Sistema Anterior ❌

```
PROBLEMA: Servo se vuelve loco
- Oscilaciones continuas
- Movimientos erráticos
- Sin control de posición
- Activaciones simultáneas
- Frutas mal clasificadas
```

### Sistema Mejorado ✅

```
SOLUCIÓN: Control preciso
✅ Movimiento suave y controlado
✅ Hold rígido en posición (1.5s)
✅ Retorno interpolado
✅ Un servo a la vez
✅ Clasificación precisa
```

---

## 🎓 Documentación Adicional

- **`MEJORAS_SERVOS_MG995.md`**: Detalles técnicos de las mejoras
- **`test_servos_mg995.py`**: Script de prueba y calibración
- **`Config_Prototipo.json`**: Configuración completa del sistema

---

## 📞 Contacto y Soporte

Si tienes problemas o preguntas:

1. Revisa la sección **Solución de Problemas** arriba
2. Ejecuta el script de prueba para diagnóstico
3. Revisa los logs del sistema
4. Verifica las conexiones físicas

---

## 🎉 ¡Sistema Listo!

Tu sistema de clasificación ahora debería funcionar perfectamente con:

- ✅ Servos MG995 controlados y estables
- ✅ Ángulos personalizados por categoría
- ✅ Sistema de hold rígido
- ✅ Retorno suave sin oscilaciones
- ✅ Protección contra activaciones simultáneas

**¡Prueba el sistema y disfruta de la clasificación automática!** 🍎🍐🍋
