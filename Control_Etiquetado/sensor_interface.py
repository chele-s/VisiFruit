# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# sensor_interface.py - Módulo para controlar los sensores de la banda
#                       transportadora (disparo de cámara y niveles de tolva).
#
# Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
# Fecha: Junio de 2025
# Descripción:
#   Este módulo maneja la inicialización y lectura de:
#   1. Un sensor de disparo para la cámara (ej: fotocelda).
#   2. Múltiples sensores ultrasónicos HC-SR04 para medir el nivel
#      de llenado de las tolvas de destino.
#   La configuración se carga desde 'config_industrial.json'.
# -----------------------------------------------------------------------------

try:
    import sys
    from pathlib import Path
    # Añadir directorio padre al path para importar utils
    parent_dir = Path(__file__).parent.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    
    from utils.gpio_wrapper import GPIO, GPIO_AVAILABLE, is_simulation_mode
    
    if is_simulation_mode():
        print("📡 Sensores: Modo simulación activo (ideal para desarrollo)")
    else:
        print("✅ Sensores: GPIO hardware activo")
        
except ImportError:
    print("⚠️ GPIO wrapper no disponible - Usando modo simulación básico para sensores")
    # Crear GPIO mock básico
    class MockGPIO:
        BCM = "bcm"
        IN = "in"
        OUT = "out"
        HIGH = 1
        LOW = 0
        PUD_UP = 1
        PUD_DOWN = 2
        PUD_OFF = 0
        RISING = "rising"
        FALLING = "falling"
        BOTH = "both"
        
        def setmode(self, mode): pass
        def setup(self, pin, mode, pull_up_down=0): pass
        def input(self, pin): return 0
        def add_event_detect(self, pin, edge, callback=None, bouncetime=None): pass
        def remove_event_detect(self, pin): pass
        def cleanup(self): pass
    
    GPIO = MockGPIO()
    GPIO_AVAILABLE = False
import time
import asyncio
import logging
import json
import os
import statistics

# Obtener logger (configurado en el script principal)
logger = logging.getLogger(__name__)

# --- Variables Globales del Módulo ---
config_data = {} # Contendrá toda la sección de sensores del config
camera_trigger_config = {}
bin_level_common_config = {}
bin_specific_configs = {} # { "CategoryName": {config_details}, ... }

# Para compensación de temperatura (si se usa)
current_temperature_c = 20.0
current_sound_speed_cm_s = 34300.0 # cm/s a 20°C

# Caché para niveles de llenado para evitar lecturas fallidas consecutivas
bin_fill_level_cache = {}

def _map_trigger_config_if_needed(src_cfg: dict) -> dict:
    """Acepta formatos alternativos (p.ej., 'trigger_sensor' del main config) y
    los convierte a la estructura interna 'camera_trigger_sensor'."""
    if not src_cfg:
        return {}
    # Caso 1: ya viene con la clave esperada
    if 'camera_trigger_sensor' in src_cfg:
        return src_cfg
    mapped = dict(src_cfg)
    trig = src_cfg.get('trigger_sensor') or src_cfg.get('laser_sensor') or src_cfg.get('yk0008_sensor')
    if trig:
        # Mapear campos comunes
        pin_bcm = trig.get('pin_bcm', trig.get('pin'))
        level = trig.get('trigger_on_state') or trig.get('trigger_level') or trig.get('edge')
        # Inferir HIGH/LOW desde 'rising'/'falling'
        if isinstance(level, str):
            lvl = level.lower()
            trigger_on_state = 'HIGH' if 'high' in lvl or 'rising' in lvl else 'LOW'
        else:
            trigger_on_state = 'LOW'
        debounce_s = (trig.get('debounce_s') if 'debounce_s' in trig else None)
        if debounce_s is None:
            debounce_ms = trig.get('debounce_time_ms', 50)
            debounce_s = float(debounce_ms) / 1000.0
        pull = trig.get('pull_up_down') or ('PUD_UP' if trig.get('pull', '').upper() == 'UP' else None)
        mapped['camera_trigger_sensor'] = {
            'pin_bcm': pin_bcm,
            'trigger_on_state': trigger_on_state,
            'pull_up_down': pull,
            'debounce_s': debounce_s
        }
    return mapped

def load_sensor_config(sensor_config_dict: dict):
    """
    Carga la configuración de todos los sensores desde un diccionario.
    """
    global config_data, camera_trigger_config, bin_level_common_config, \
           bin_specific_configs, current_temperature_c, current_sound_speed_cm_s
    try:
        if not sensor_config_dict:
            logger.error("El diccionario de configuración de sensores está vacío.")
            return False
            
        # Permitir distintos esquemas (main config vs industrial)
        config_data = _map_trigger_config_if_needed(sensor_config_dict)
        
        # Cargar configuración del sensor de disparo de cámara
        camera_trigger_config = config_data.get('camera_trigger_sensor', {})
        if not camera_trigger_config.get('pin_bcm'):
            logger.warning("No se especificó 'pin_bcm' para 'camera_trigger_sensor'. Funcionalidad limitada.")
        else:
            logger.info(f"Configuración de sensor de disparo de cámara cargada: {camera_trigger_config}")

        # Cargar configuración de sensores de nivel de tolva
        bin_sensors_config = config_data.get('bin_level_sensors', {})
        bin_level_common_config = bin_sensors_config.get('settings_common', {
            # Valores por defecto si no están en config
            "sound_speed_cm_s": 34300,
            "readings_per_measurement": 3,
            "measurement_timeout_s": 0.1, # Timeout más corto para HC-SR04
            "reading_interval_s": 0.05,
            "use_temperature_compensation": False,
            "default_temperature_c": 20.0
        })
        current_temperature_c = bin_level_common_config.get("default_temperature_c", 20.0)
        if bin_level_common_config.get("use_temperature_compensation", False):
            current_sound_speed_cm_s = _calculate_sound_speed_with_temp(current_temperature_c)
        else:
            current_sound_speed_cm_s = bin_level_common_config.get("sound_speed_cm_s", 34300)

        bin_specific_configs = bin_sensors_config.get('bins', {})
        if not bin_specific_configs:
            logger.warning("No se encontraron configuraciones específicas para 'bins' en 'bin_level_sensors'.")
        else:
            for bin_name, s_config in bin_specific_configs.items():
                # Heredar/validar parámetros comunes
                for key, val in bin_level_common_config.items():
                    if key not in s_config: # Si no está en la config específica, no lo añadimos aquí
                                            # se usará el común al leer.
                        pass
                logger.info(f"Configuración de sensor de nivel para tolva '{bin_name}' cargada.")
        
        logger.info("Configuración de sensores cargada exitosamente.")
        return True

    except Exception as e:
        logger.error(f"Error cargando la configuración de sensores: {e}", exc_info=True)
        return False

def setup_sensor_gpio():
    """
    Configura los pines GPIO para todos los sensores definidos.
    Debe llamarse después de load_sensor_config().
    """
    if not config_data: # Verifica si config_data tiene algo
        logger.error("Configuración de sensores no cargada. Ejecute load_sensor_config() primero.")
        return False
    
    try:
        # Asumiendo que GPIO.setmode(GPIO.BCM) se llama en el script principal
        # GPIO.setwarnings(False)

        # Configurar sensor de disparo de cámara
        if camera_trigger_config.get('pin_bcm') is not None:
            pin = camera_trigger_config['pin_bcm']
            pull_up_down_str = camera_trigger_config.get('pull_up_down', None)
            pud = GPIO.PUD_OFF
            if pull_up_down_str == "PUD_UP":
                pud = GPIO.PUD_UP
            elif pull_up_down_str == "PUD_DOWN":
                pud = GPIO.PUD_DOWN
            
            GPIO.setup(pin, GPIO.IN, pull_up_down=pud)
            logger.info(f"GPIO {pin} (Sensor Disparo Cámara) configurado como ENTRADA (pull: {pull_up_down_str}).")

        # Configurar sensores de nivel de tolva (HC-SR04)
        for bin_name, s_config in bin_specific_configs.items():
            trig_pin = s_config.get('trig_pin_bcm')
            echo_pin = s_config.get('echo_pin_bcm')
            if trig_pin is not None and echo_pin is not None:
                GPIO.setup(trig_pin, GPIO.OUT, initial=GPIO.LOW)
                GPIO.setup(echo_pin, GPIO.IN)
                logger.info(f"GPIOs para sensor de nivel tolva '{bin_name}' (TRIG={trig_pin}, ECHO={echo_pin}) configurados.")
            else:
                logger.warning(f"Pines TRIG/ECHO no definidos para sensor de tolva '{bin_name}'.")
        
        logger.info("Todos los GPIOs de sensores configurados.")
        # Pequeña pausa para estabilización de sensores ultrasónicos si es necesario
        time.sleep(bin_level_common_config.get("stabilization_time_s", 0.2))
        return True
    except Exception as e:
        logger.error(f"Error configurando GPIOs para sensores: {e}", exc_info=True)
        return False

# --- Funciones para Sensor de Disparo de Cámara ---

def check_camera_trigger():
    """
    Verifica el estado actual del sensor de disparo de la cámara.
    Devuelve True si está activado, False en caso contrario.
    """
    pin = camera_trigger_config.get('pin_bcm')
    if pin is None:
        # logger.debug("Sensor de disparo de cámara no configurado, devolviendo False.")
        return False # O lanzar excepción, o manejar de otra forma

    trigger_on = camera_trigger_config.get('trigger_on_state', 'LOW')
    current_state = GPIO.input(pin)

    if trigger_on == 'LOW':
        return current_state == GPIO.LOW
    else: # trigger_on == 'HIGH'
        return current_state == GPIO.HIGH

def wait_for_camera_trigger(timeout_s=None):
    """
    Espera (bloqueante) hasta que el sensor de disparo de la cámara se active
    o hasta que se alcance el timeout.
    Devuelve True si se activó, False si hubo timeout.
    """
    pin = camera_trigger_config.get('pin_bcm')
    if pin is None:
        logger.warning("Sensor de disparo de cámara no configurado. Simulará activación tras input.")
        input("Presiona Enter para simular disparo de cámara...")
        return True
    
    trigger_on_level = GPIO.LOW if camera_trigger_config.get('trigger_on_state', 'LOW') == 'LOW' else GPIO.HIGH
    debounce_s = camera_trigger_config.get('debounce_s', 0.05)
    
    logger.debug(f"Esperando disparo de cámara en GPIO {pin} (activación en {camera_trigger_config.get('trigger_on_state', 'LOW')})...")
    
    start_time = time.time()
    while True:
        if GPIO.input(pin) == trigger_on_level:
            time.sleep(debounce_s) # Anti-rebote
            if GPIO.input(pin) == trigger_on_level: # Confirmar después del debounce
                logger.info(f"Disparo de cámara detectado en GPIO {pin}.")
                return True
        
        if timeout_s is not None and (time.time() - start_time) > timeout_s:
            logger.debug(f"Timeout esperando disparo de cámara en GPIO {pin}.")
            return False
        
        time.sleep(0.005) # Pequeña pausa para no saturar CPU

# --- Funciones para Sensores de Nivel de Tolva (Ultrasónicos HC-SR04) ---

def _calculate_sound_speed_with_temp(temperature_c):
    """Calcula la velocidad del sonido ajustada por temperatura (cm/s)."""
    return (331.3 + 0.606 * temperature_c) * 100

def set_current_temperature(temperature_c):
    """Actualiza la temperatura ambiente y recalcula la velocidad del sonido si la compensación está activa."""
    global current_temperature_c, current_sound_speed_cm_s
    current_temperature_c = temperature_c
    if bin_level_common_config.get("use_temperature_compensation", False):
        current_sound_speed_cm_s = _calculate_sound_speed_with_temp(temperature_c)
        logger.info(f"Temperatura actualizada a {temperature_c}°C. Nueva velocidad del sonido: {current_sound_speed_cm_s:.2f} cm/s.")
    else:
        logger.debug("Compensación de temperatura desactivada, `set_current_temperature` no cambia la velocidad del sonido.")

def _get_distance_cm_ultrasonic(trig_pin, echo_pin, retries=1):
    """Mide la distancia para un sensor ultrasónico específico."""
    timeout = bin_level_common_config.get("measurement_timeout_s", 0.1)
    
    for attempt in range(retries + 1):
        try:
            GPIO.output(trig_pin, GPIO.LOW)
            time.sleep(0.000002) # 2µs de pausa antes del pulso

            GPIO.output(trig_pin, GPIO.HIGH)
            time.sleep(0.00001) # Pulso TRIG de 10µs
            GPIO.output(trig_pin, GPIO.LOW)

            pulse_start_time = time.time()
            loop_start_time = pulse_start_time

            while GPIO.input(echo_pin) == GPIO.LOW:
                pulse_start_time = time.time()
                if pulse_start_time - loop_start_time > timeout:
                    if attempt < retries: continue
                    # logger.debug(f"Timeout (TRIG={trig_pin},ECHO={echo_pin}): No se detectó inicio de pulso ECHO.")
                    return None
            
            pulse_end_time = time.time()
            loop_start_time = pulse_end_time
            while GPIO.input(echo_pin) == GPIO.HIGH:
                pulse_end_time = time.time()
                if pulse_end_time - loop_start_time > timeout: # El pulso ECHO no debería ser tan largo
                    if attempt < retries: continue
                    # logger.debug(f"Timeout (TRIG={trig_pin},ECHO={echo_pin}): Pulso ECHO demasiado largo.")
                    return None # O un valor muy pequeño si se asume objeto muy cerca

            if pulse_start_time and pulse_end_time > pulse_start_time:
                pulse_duration = pulse_end_time - pulse_start_time
                distance = (pulse_duration * current_sound_speed_cm_s) / 2
                return distance
            # else:
                # logger.debug(f"Error en tiempos de pulso para TRIG={trig_pin}, ECHO={echo_pin}")

        except RuntimeError as e: # Captura errores si GPIO no está configurado, etc.
            logger.error(f"RuntimeError midiendo distancia (TRIG={trig_pin},ECHO={echo_pin}): {e}")
            return None # Importante devolver None para que no falle el promedio
        except Exception as e:
            logger.error(f"Excepción midiendo distancia (TRIG={trig_pin},ECHO={echo_pin}): {e}", exc_info=False) # Poner True para debug
            # No reintentar en excepciones generales, podría ser un problema de configuración
            return None
        
        if attempt < retries:
            time.sleep(0.01) # Pequeña pausa entre reintentos

    return None # Todos los intentos fallaron

def _get_avg_distance_ultrasonic(trig_pin, echo_pin):
    """Obtiene un promedio (mediana) de múltiples lecturas de distancia."""
    num_readings = bin_level_common_config.get("readings_per_measurement", 3)
    reading_interval = bin_level_common_config.get("reading_interval_s", 0.05)
    readings = []
    
    for _ in range(num_readings):
        dist = _get_distance_cm_ultrasonic(trig_pin, echo_pin, retries=0) # Reintentos ya en _get_distance_cm_ultrasonic
        if dist is not None:
            readings.append(dist)
        if num_readings > 1 : time.sleep(reading_interval)
            
    if not readings:
        return None
    
    if len(readings) >= 3: # Usar mediana si hay suficientes datos para robustez
        return statistics.median(readings)
    else: # Promedio simple para menos de 3 lecturas válidas
        return sum(readings) / len(readings)

def _calculate_fill_percentage(distance_cm, bin_depth_cm_val):
    """Calcula el porcentaje de llenado a partir de la distancia medida."""
    if distance_cm is None or bin_depth_cm_val <= 0:
        return None
        
    # Distancia es desde el sensor hasta el contenido.
    # Espacio lleno = Profundidad total - distancia medida (espacio vacío)
    filled_space = bin_depth_cm_val - distance_cm
    
    # Asegurar que el espacio lleno no sea negativo (objeto más allá del fondo)
    # o mayor que la profundidad (sensor reporta algo muy cerca/error)
    filled_space = max(0, min(filled_space, bin_depth_cm_val))
    
    fill_percentage = (filled_space / bin_depth_cm_val) * 100
    return round(max(0, min(100, fill_percentage)), 1)


def get_bin_fill_level(category_name):
    """
    Obtiene el nivel de llenado (0-100%) para una tolva específica.
    Devuelve el valor de caché si la lectura actual falla.
    """
    global bin_fill_level_cache
    if category_name not in bin_specific_configs:
        logger.warning(f"No hay configuración de sensor de nivel para la tolva '{category_name}'.")
        return None

    s_config = bin_specific_configs[category_name]
    trig_pin = s_config.get('trig_pin_bcm')
    echo_pin = s_config.get('echo_pin_bcm')
    depth = s_config.get('bin_depth_cm', bin_level_common_config.get('bin_depth_cm', 50.0)) # Usa específico o común

    if trig_pin is None or echo_pin is None:
        logger.error(f"Pines TRIG/ECHO no configurados para tolva '{category_name}'.")
        return bin_fill_level_cache.get(category_name) # Devuelve caché si existe

    distance = _get_avg_distance_ultrasonic(trig_pin, echo_pin)
    fill_percentage = _calculate_fill_percentage(distance, depth)

    if fill_percentage is not None:
        bin_fill_level_cache[category_name] = fill_percentage # Actualizar caché
        logger.debug(f"Nivel tolva '{category_name}': {fill_percentage}% (Dist: {distance:.1f}cm)")
        return fill_percentage
    else:
        logger.warning(f"Fallo al leer sensor de nivel para tolva '{category_name}'. Usando valor de caché si existe.")
        return bin_fill_level_cache.get(category_name) # Devuelve el último valor bueno

def get_all_bin_fill_levels():
    """Obtiene el nivel de llenado para todas las tolvas configuradas."""
    levels = {}
    for bin_name in bin_specific_configs.keys():
        levels[bin_name] = get_bin_fill_level(bin_name)
    return levels

def cleanup_sensor_gpio():
    """Libera los recursos GPIO utilizados por los sensores."""
    logger.info("Limpiando GPIOs de los sensores...")
    # La limpieza general de GPIO.cleanup() en main_sistema_banda.py
    # se encargará de todos los pines. Este módulo no necesita llamar
    # a GPIO.cleanup() por sí mismo si es parte de un sistema más grande.
    logger.info("Limpieza de GPIOs de sensores completada (no se requiere acción específica aquí si se limpia en main).")


class SensorInterface:
    """
    Interfaz principal para el manejo de sensores del sistema.
    
    Esta clase encapsula toda la funcionalidad de sensores incluyendo:
    - Sensor de disparo de cámara
    - Sensores de nivel de tolva
    - Configuración y manejo de GPIO
    """
    
    def __init__(self, trigger_callback=None):
        """
        Inicializa la interfaz de sensores.
        
        Args:
            trigger_callback: Función callback para cuando se active el trigger
        """
        self.trigger_callback = trigger_callback
        self.is_initialized = False
        self.trigger_enabled = False
        self.config = {} # Se cargará en initialize
        self._poll_task = None
        self._last_trigger_state = None
        self._trigger_event_count = 0
        self._auto_calibrating = False
        
        logger.info("SensorInterface instanciada")
    
    def initialize(self, sensor_config: dict) -> bool:
        """
        Inicializa todos los sensores del sistema.
        
        Args:
            sensor_config: El diccionario con la configuración de los sensores.
            
        Returns:
            bool: True si la inicialización fue exitosa
        """
        self.config = sensor_config
        try:
            # Cargar configuración de sensores
            if not load_sensor_config(self.config):
                logger.error("Error cargando configuración de sensores")
                return False
            
            # Configurar GPIO para sensores
            if not setup_sensor_gpio():
                logger.error("Error configurando GPIO para sensores")
                return False
            
            self.is_initialized = True
            logger.info("SensorInterface inicializada correctamente")
            return True
            
        except Exception as e:
            logger.error(f"Error inicializando SensorInterface: {e}")
            return False
    
    def enable_trigger_monitoring(self):
        """Habilita el monitoreo del sensor de trigger."""
        if not self.is_initialized:
            logger.warning("SensorInterface no inicializada")
            return False
        
        try:
            self.trigger_enabled = True
            
            # Configurar detección de eventos si está disponible el callback
            if self.trigger_callback and camera_trigger_config.get('pin_bcm'):
                pin = camera_trigger_config['pin_bcm']
                # Elegir borde compatible con wrapper
                trigger_edge = getattr(GPIO, 'FALLING', 'falling') if camera_trigger_config.get('trigger_on_state', 'LOW') == 'LOW' else getattr(GPIO, 'RISING', 'rising')
                debounce_ms = int(camera_trigger_config.get('debounce_s', 0.05) * 1000)
                
                def _trigger_event_handler(channel):
                    """Handler interno para eventos de trigger."""
                    try:
                        self._trigger_event_count += 1
                        if self.trigger_enabled and self.trigger_callback:
                            self.trigger_callback()
                    except Exception as e:
                        logger.error(f"Error en callback de trigger: {e}")
                
                # Algunos backends pueden no exponer add_event_detect/remove_event_detect
                if hasattr(GPIO, 'add_event_detect'):
                    GPIO.add_event_detect(pin, trigger_edge, callback=_trigger_event_handler, bouncetime=debounce_ms)
                    # Guardar bandera para limpieza segura
                    self._event_detect_registered = True
                    self._event_detect_pin = pin
                else:
                    # Iniciar bucle de polling asíncrono
                    if self._poll_task is None or self._poll_task.done():
                        self._poll_task = asyncio.create_task(self._poll_trigger_loop())
                    logger.warning("Backend GPIO sin soporte de eventos; usando loop de polling")
                logger.info(f"Monitoreo de trigger habilitado en GPIO {pin}")
                # Iniciar auto-calibración de borde/pull si no hay eventos
                try:
                    if not self._auto_calibrating:
                        asyncio.create_task(self._auto_calibrate_trigger())
                except Exception:
                    pass
            
            return True
            
        except Exception as e:
            logger.error(f"Error habilitando monitoreo de trigger: {e}")
            return False
    
    def disable_trigger_monitoring(self):
        """Deshabilita el monitoreo del sensor de trigger."""
        try:
            self.trigger_enabled = False
            
            if camera_trigger_config.get('pin_bcm'):
                pin = camera_trigger_config['pin_bcm']
                # Solo intentar si el backend soporta la API
                if hasattr(GPIO, 'remove_event_detect'):
                    try:
                        GPIO.remove_event_detect(pin)
                    except Exception as e:
                        logger.debug(f"Ignorando error al remover evento: {e}")
                else:
                    # Detener polling si está activo
                    if self._poll_task:
                        self._poll_task.cancel()
                        self._poll_task = None
                    logger.debug("Backend GPIO sin remove_event_detect; detenido polling")
                logger.info(f"Monitoreo de trigger deshabilitado en GPIO {pin}")
            
        except Exception as e:
            logger.error(f"Error deshabilitando monitoreo de trigger: {e}")
    
    def check_trigger_state(self) -> bool:
        """
        Verifica el estado actual del sensor de trigger.
        
        Returns:
            bool: True si el trigger está activado
        """
        if not self.is_initialized:
            return False
        
        return check_camera_trigger()
    
    def wait_for_trigger(self, timeout_s=None) -> bool:
        """
        Espera a que se active el sensor de trigger.
        
        Args:
            timeout_s: Tiempo máximo de espera en segundos
            
        Returns:
            bool: True si se detectó trigger, False si hubo timeout
        """
        if not self.is_initialized:
            return False
        
        return wait_for_camera_trigger(timeout_s)
    
    def get_bin_fill_levels(self) -> dict:
        """
        Obtiene los niveles de llenado de todas las tolvas.
        
        Returns:
            dict: Niveles de llenado por categoría
        """
        if not self.is_initialized:
            return {}
        
        return get_all_bin_fill_levels()
    
    def get_bin_fill_level(self, category: str) -> float:
        """
        Obtiene el nivel de llenado de una tolva específica.
        
        Args:
            category: Nombre de la categoría/tolva
            
        Returns:
            float: Nivel de llenado (0-100%) o None si hay error
        """
        if not self.is_initialized:
            return None
        
        return get_bin_fill_level(category)
    
    def update_temperature(self, temperature_c: float):
        """
        Actualiza la temperatura ambiente para compensación en sensores ultrasónicos.
        
        Args:
            temperature_c: Temperatura en grados Celsius
        """
        if not self.is_initialized:
            return
        
        set_current_temperature(temperature_c)
    
    def get_status(self) -> dict:
        """
        Obtiene el estado completo del sistema de sensores.
        
        Returns:
            dict: Estado y métricas de todos los sensores
        """
        return {
            "is_initialized": self.is_initialized,
            "trigger_enabled": self.trigger_enabled,
            "trigger_config": camera_trigger_config.copy(),
            "bin_sensors_config": bin_specific_configs.copy(),
            "current_temperature_c": current_temperature_c,
            "bin_fill_levels": self.get_bin_fill_levels() if self.is_initialized else {}
        }
    
    def shutdown(self):
        """Cierra y limpia todos los recursos de sensores."""
        try:
            self.disable_trigger_monitoring()
            cleanup_sensor_gpio()
            self.is_initialized = False
            logger.info("SensorInterface cerrada correctamente")
            
        except Exception as e:
            logger.error(f"Error cerrando SensorInterface: {e}")

    async def _poll_trigger_loop(self):
        """Bucle de polling para detectar trigger cuando no hay soporte de eventos."""
        try:
            pin = camera_trigger_config.get('pin_bcm')
            if pin is None:
                return
            trigger_on_low = camera_trigger_config.get('trigger_on_state', 'LOW') == 'LOW'
            debounce_s = float(camera_trigger_config.get('debounce_s', 0.05))
            last_state = GPIO.input(pin)
            last_change_time = time.time()
            while self.trigger_enabled and self.is_initialized:
                current = GPIO.input(pin)
                now = time.time()
                if current != last_state:
                    last_change_time = now
                    last_state = current
                else:
                    # Si estable y coincide con trigger y cumplió debounce
                    if ((trigger_on_low and current == GPIO.LOW) or (not trigger_on_low and current == GPIO.HIGH)):
                        if (now - last_change_time) >= debounce_s:
                            try:
                                self._trigger_event_count += 1
                                if self.trigger_enabled and self.trigger_callback:
                                    self.trigger_callback()
                            finally:
                                # Evitar múltiples callbacks continuos hasta liberar el haz
                                await asyncio.sleep(debounce_s)
                                # Esperar a que cambie el estado
                                while GPIO.input(pin) == current and self.trigger_enabled and self.is_initialized:
                                    await asyncio.sleep(0.005)
                                last_state = GPIO.input(pin)
                                last_change_time = time.time()
                await asyncio.sleep(0.002)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error en polling de trigger: {e}")

    async def _auto_calibrate_trigger(self):
        """Si no hay eventos en una ventana corta, invertir borde y/o pull-up/down."""
        if self._auto_calibrating:
            return
        self._auto_calibrating = True
        try:
            # Esperar ventana inicial
            await asyncio.sleep(float(camera_trigger_config.get('debounce_s', 0.05)) + 2.0)
            if not self.trigger_enabled or not self.is_initialized:
                return
            if self._trigger_event_count > 0:
                return
            pin = camera_trigger_config.get('pin_bcm')
            if pin is None:
                return
            logger.warning("Sin eventos del láser en ventana inicial: intentando invertir borde")
            # Invertir trigger_on_state
            current_state = camera_trigger_config.get('trigger_on_state', 'LOW')
            new_state = 'HIGH' if current_state == 'LOW' else 'LOW'
            camera_trigger_config['trigger_on_state'] = new_state
            # Reconfigurar monitoreo
            try:
                if hasattr(GPIO, 'remove_event_detect') and getattr(self, '_event_detect_registered', False):
                    try:
                        GPIO.remove_event_detect(pin)
                    except Exception:
                        pass
                    # Reagregar con nuevo borde
                    trigger_edge = getattr(GPIO, 'FALLING', 'falling') if new_state == 'LOW' else getattr(GPIO, 'RISING', 'rising')
                    debounce_ms = int(camera_trigger_config.get('debounce_s', 0.05) * 1000)

                    def _trigger_event_handler2(channel):
                        try:
                            self._trigger_event_count += 1
                            if self.trigger_enabled and self.trigger_callback:
                                self.trigger_callback()
                        except Exception as e:
                            logger.error(f"Error en callback de trigger: {e}")

                    GPIO.add_event_detect(pin, trigger_edge, callback=_trigger_event_handler2, bouncetime=debounce_ms)
                    self._event_detect_registered = True
                    self._event_detect_pin = pin
                else:
                    # Polling: nada extra que hacer; el bucle leerá el nuevo estado objetivo
                    pass
            except Exception as e:
                logger.debug(f"Error reconfigurando borde del trigger: {e}")
            # Esperar otra ventana
            await asyncio.sleep(2.0)
            if self._trigger_event_count > 0:
                logger.info("Auto-calibración: eventos detectados tras invertir borde")
                return
            # Intentar cambiar pull-up/down si está definido
            pull = camera_trigger_config.get('pull_up_down', None)
            try:
                if pull in ("PUD_UP", "PUD_DOWN"):
                    new_pull = "PUD_DOWN" if pull == "PUD_UP" else "PUD_UP"
                    camera_trigger_config['pull_up_down'] = new_pull
                    pud = GPIO.PUD_UP if new_pull == "PUD_UP" else GPIO.PUD_DOWN
                    GPIO.setup(pin, GPIO.IN, pull_up_down=pud)
                    logger.warning(f"Auto-calibración: cambiando pull a {new_pull}")
            except Exception as e:
                logger.debug(f"Error cambiando pull: {e}")
        finally:
            self._auto_calibrating = False

# --- Código de Prueba ---
if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    TEST_CONFIG_FILE_SENSORS = 'config_industrial_sensors_test.json'
    if not os.path.exists(TEST_CONFIG_FILE_SENSORS):
        logger.info(f"Creando archivo de config de prueba para sensores: {TEST_CONFIG_FILE_SENSORS}")
        test_sensor_cfg_content = {
            "sensors_settings": {
                "camera_trigger_sensor": {
                    "pin_bcm": 17, # Ejemplo, ajusta a un pin libre
                    "trigger_on_state": "LOW",
                    "pull_up_down": "PUD_UP",
                    "debounce_s": 0.1
                },
                "bin_level_sensors": {
                    "settings_common": {
                        "sound_speed_cm_s": 34300,
                        "readings_per_measurement": 5,
                        "measurement_timeout_s": 0.1,
                        "reading_interval_s": 0.05,
                        "use_temperature_compensation": True,
                        "default_temperature_c": 22.5,
                        "stabilization_time_s": 0.2
                    },
                    "bins": {
                        "Metal": { # Asegúrate que estos pines estén libres y conectados a un HC-SR04
                            "trig_pin_bcm": 23,
                            "echo_pin_bcm": 24,
                            "bin_depth_cm": 50.0
                        },
                        "Plastic": {
                            "trig_pin_bcm": 25, # Ejemplo, ajusta
                            "echo_pin_bcm": 8,  # Ejemplo, ajusta
                            "bin_depth_cm": 40.0
                        }
                    }
                }
            }
        }
        with open(TEST_CONFIG_FILE_SENSORS, 'w') as f:
            json.dump(test_sensor_cfg_content, f, indent=4)
    
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        if load_sensor_config(config_file=TEST_CONFIG_FILE_SENSORS):
            if setup_sensor_gpio():
                logger.info("=== Prueba de Interfaz de Sensores ===")
                
                # Probar sensor de disparo de cámara
                logger.info("\n--- Probando Sensor de Disparo de Cámara ---")
                logger.info(f"Por favor, activa el sensor en GPIO {camera_trigger_config.get('pin_bcm')}...")
                if wait_for_camera_trigger(timeout_s=10.0):
                    logger.info("¡Sensor de disparo de cámara FUNCIONA!")
                else:
                    logger.warning("Sensor de disparo de cámara NO detectado o timeout.")
                logger.info(f"Estado actual del trigger: {check_camera_trigger()}")
                time.sleep(1)

                # Probar sensores de nivel de tolva
                logger.info("\n--- Probando Sensores de Nivel de Tolva ---")
                if bin_specific_configs:
                    set_current_temperature(25.0) # Probar cambio de temperatura
                    
                    for i in range(3): # Leer varias veces
                        levels = get_all_bin_fill_levels()
                        for bin_name, level in levels.items():
                            if level is not None:
                                logger.info(f"Lectura {i+1}: Nivel tolva '{bin_name}': {level:.1f}%")
                            else:
                                logger.warning(f"Lectura {i+1}: No se pudo leer el nivel para tolva '{bin_name}'.")
                        time.sleep(1)
                else:
                    logger.info("No hay sensores de nivel de tolva configurados para probar.")
            else:
                logger.error("Fallo al configurar GPIOs para sensores.")
        else:
            logger.error("Fallo al cargar la configuración de sensores.")

    except KeyboardInterrupt:
        logger.info("Prueba interrumpida por el usuario.")
    except Exception as e:
        logger.error(f"Error durante la prueba de sensores: {e}", exc_info=True)
    finally:
        logger.info("Limpiando GPIO al final de la prueba de sensores...")
        cleanup_sensor_gpio()
        GPIO.cleanup() # Limpieza final de todos los canales
        logger.info("=== Prueba de Sensores Finalizada ===")
