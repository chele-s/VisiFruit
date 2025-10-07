# 🚀 Mejoras del Sistema de Servos MG995 - Prototipo VisiFruit

## 📋 Resumen de Mejoras

Se ha implementado un sistema mejorado de control de servomotores MG995 para el prototipo de clasificación de frutas, eliminando los problemas de oscilación y movimientos erráticos.

### 🎯 Problemas Solucionados

1. **Servos "volviéndose locos"** - Oscilaciones y movimientos erráticos
2. **Falta de control preciso** - Los servos no mantenían posición
3. **Activaciones simultáneas** - Múltiples servos activándose al mismo tiempo
4. **Retorno brusco** - Movimiento violento al regresar a posición inicial

---

## 🔧 Cambios Técnicos Implementados

### 1. Sistema de Hold Rígido

**Antes:**
```python
# PWM se desactivaba inmediatamente
await self.set_servo_angle(category, angle)
await asyncio.sleep(0.02)
pwm.ChangeDutyCycle(0)  # ❌ Servo pierde posición
```

**Ahora:**
```python
# PWM se mantiene activo durante hold
await self.set_servo_angle(category, angle, hold=True)
await asyncio.sleep(hold_duration)  # ✅ Servo mantiene posición rígida
pwm.ChangeDutyCycle(duty_cycle)    # Señal activa
```

### 2. Retorno Suave a Posición Inicial

**Antes:**
```python
# Movimiento brusco
await self.set_servo_angle(category, default_angle)
```

**Ahora:**
```python
# Movimiento interpolado en 10 pasos
for i in range(10):
    intermediate_angle = current + (step_size * (i + 1))
    await self.set_servo_angle(category, intermediate_angle, hold=True)
    await asyncio.sleep(0.05)  # Movimiento suave
```

### 3. Protección contra Activaciones Simultáneas

**Implementación:**
```python
async with self._servo_locks[category]:  # Lock por servo
    self._active_servos.add(category)
    try:
        # Activación controlada
        ...
    finally:
        self._active_servos.discard(category)
```

### 4. Procesamiento Secuencial de Clasificaciones

**Antes:**
```python
# Todas las clasificaciones se procesaban en paralelo
for event in pending_events:
    await self._classify_fruit(event)  # ❌ Simultáneas
```

**Ahora:**
```python
# Procesamiento secuencial con pausas
for event in events_to_process:
    await self._classify_fruit(event)
    await asyncio.sleep(0.2)  # ✅ Una a la vez
```

---

## 📐 Configuración de Ángulos Actualizada

### Config_Prototipo.json

```json
{
  "servo_settings": {
    "apple": {
      "pin_bcm": 5,
      "default_angle": 90,      // Posición neutra
      "activation_angle": -10,  // Gira -100° (normalizado a 0°)
      "hold_duration_s": 1.5,   // Mantiene rígido 1.5s
      "return_smoothly": true   // Retorno suave activado
    },
    "pear": {
      "pin_bcm": 6,
      "default_angle": 90,
      "activation_angle": 180,  // Gira +90°
      "hold_duration_s": 1.5,
      "return_smoothly": true
    },
    "lemon": {
      "pin_bcm": 7,
      "default_angle": 90,
      "activation_angle": 10,   // Gira -80°
      "hold_duration_s": 1.5,
      "return_smoothly": true
    }
  }
}
```

### Explicación de Ángulos

- **default_angle (90°)**: Posición de reposo - pieza de madera en posición neutra
- **activation_angle**: Posición cuando se activa para clasificar
- **Movimiento efectivo**: 
  - 🍎 Manzanas: 90° → -10° (normalizado a 0°) = **-100° de movimiento**
  - 🍐 Peras: 90° → 180° = **+90° de movimiento**
  - 🍋 Limones: 90° → 10° = **-80° de movimiento**

---

## 🔄 Secuencia de Activación Mejorada

### Fase 1: Movimiento a Posición de Clasificación
```
1. Verificar que servo no está activo (lock)
2. Verificar intervalo mínimo (0.5s)
3. Adquirir lock exclusivo del servo
4. Mover a activation_angle con PWM activo
5. Tiempo: ~0.3s (velocidad MG995: 0.2s/60°)
```

### Fase 2: Hold Rígido
```
1. Mantener PWM activo en activation_angle
2. Servo permanece RÍGIDO en posición
3. Duración: hold_duration_s (1.5s configurado)
4. La pieza de madera empuja la fruta correctamente
```

### Fase 3: Retorno Suave
```
1. Interpolar entre activation_angle y default_angle
2. 10 pasos de 50ms cada uno
3. Movimiento suave sin sacudidas
4. Tiempo total: ~0.5s
```

### Fase 4: Desactivación PWM
```
1. Llegar a default_angle
2. Desactivar PWM (ChangeDutyCycle(0))
3. Evitar oscilaciones y ruido
4. Liberar lock del servo
```

**Tiempo Total por Clasificación:** ~2.3 segundos

---

## 🧪 Cómo Probar las Mejoras

### Ejecutar Script de Prueba

```bash
cd Prototipo_Clasificador
python test_servos_mg995.py
```

### Opciones de Prueba Disponibles

1. **Prueba Individual**
   - Prueba un servo específico
   - Verifica movimiento, hold y retorno

2. **Prueba Secuencial**
   - Prueba los 3 servos en orden
   - Verifica coordinación

3. **Prueba de Activación Rápida**
   - Verifica protección contra activaciones simultáneas
   - Intenta 3 activaciones rápidas

4. **Modo Calibración**
   - Mueve servos manualmente a cualquier ángulo
   - Útil para ajustar posiciones

### Verificación Visual

Al probar cada servo, verifica:

✅ **Movimiento inicial rápido** - Sin oscilaciones  
✅ **Hold rígido** - Servo firme por 1.5s  
✅ **Retorno suave** - Sin sacudidas  
✅ **Parada completa** - Sin vibraciones al final  

---

## 📊 Monitoreo y Logs

### Log de Activación Exitosa

```
============================================================
🎯 Activando servo apple
   📐 90° → -10° (Δ -100°)
   ⏱️ Hold: 1.5s | Total: 2.0s
   🔒 Manteniendo posición rígida por 1.5s...
   🔄 Retornando suavemente a 90°...
   ✅ Servo apple completado exitosamente
============================================================
```

### Estadísticas del Sistema

```python
status = controller.get_status()
print(f"Total activaciones: {status['total_activations']}")
print(f"Servos activos: {status['servos']}")
```

---

## ⚙️ Parámetros Ajustables

### En Config_Prototipo.json

```json
{
  "timing": {
    "classification_delay_s": 0.5,        // Delay antes de clasificar
    "min_servo_activation_interval_s": 2.0  // Intervalo mínimo entre servos
  },
  
  "servo_settings": {
    "apple": {
      "activation_duration_s": 2.0,  // Duración total de activación
      "hold_duration_s": 1.5,        // Tiempo manteniendo posición
      "return_smoothly": true        // Activar retorno suave
    }
  }
}
```

### Ajustes Recomendados

- **hold_duration_s**: 
  - ⬆️ Aumentar si la fruta no se clasifica completamente
  - ⬇️ Reducir para mayor velocidad (mínimo 1.0s)

- **activation_angle**: 
  - Calibrar según posición física de la pieza de madera
  - Usar modo de calibración para encontrar ángulo óptimo

- **min_servo_activation_interval_s**:
  - ⬆️ Aumentar si hay errores de activación simultánea
  - ⬇️ Reducir para mayor throughput (mínimo 0.5s)

---

## 🐛 Solución de Problemas

### Servo oscila o vibra

**Causa:** PWM no se está desactivando correctamente  
**Solución:**
```python
# Verificar que PWM se desactive al final
pwm.ChangeDutyCycle(0)
```

### Servo no mantiene posición

**Causa:** hold=False en set_servo_angle  
**Solución:**
```python
# Usar hold=True durante activación
await self.set_servo_angle(category, angle, hold=True)
```

### Múltiples servos activos simultáneamente

**Causa:** Lock no está funcionando  
**Solución:**
```python
# Verificar que _servo_locks está inicializado
self._servo_locks[category] = asyncio.Lock()
```

### Movimiento brusco al retornar

**Causa:** return_smoothly desactivado  
**Solución:**
```json
{
  "return_smoothly": true  // En configuración
}
```

---

## 📈 Comparación Antes/Después

| Característica | Antes ❌ | Ahora ✅ |
|----------------|----------|----------|
| **Oscilaciones** | Frecuentes | Ninguna |
| **Hold rígido** | No | Sí (1.5s) |
| **Retorno suave** | No | Sí (10 pasos) |
| **Protección simultánea** | No | Sí (locks) |
| **Control de ángulos** | Básico (0-90) | Preciso (-100, +90, -80) |
| **Desactivación PWM** | Inmediata | Controlada |
| **Procesamiento** | Paralelo | Secuencial |

---

## 🎓 Próximos Pasos

### Optimización Adicional

1. **Ajuste fino de ángulos**
   - Usar modo calibración para encontrar ángulos óptimos
   - Probar con frutas reales

2. **Timing del sistema**
   - Ajustar classification_delay_s según velocidad de banda
   - Optimizar hold_duration_s para máximo throughput

3. **Monitoreo de rendimiento**
   - Registrar tiempos de activación
   - Detectar degradación del servo

### Mantenimiento

- Revisar servos cada 1000 activaciones
- Verificar que las piezas de madera estén bien fijadas
- Comprobar conexiones y alimentación (6V recomendado)

---

## 📞 Soporte

Si encuentras problemas:

1. Ejecuta `test_servos_mg995.py` para diagnóstico
2. Revisa los logs en `logs/prototipo_clasificador.log`
3. Verifica la alimentación de los servos (4.8-7.2V)
4. Comprueba las conexiones GPIO

---

**¡El sistema ahora debería funcionar sin oscilaciones!** 🎉
