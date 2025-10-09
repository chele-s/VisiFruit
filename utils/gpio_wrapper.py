# utils/gpio_wrapper.py
"""
GPIO Wrapper para compatibilidad universal
===========================================

Módulo wrapper que proporciona compatibilidad entre:
- Windows (simulación para desarrollo)  
- Raspberry Pi 5 (lgpio)
- Raspberry Pi anteriores (RPi.GPIO como fallback)

Uso:
    from utils.gpio_wrapper import GPIO, GPIO_AVAILABLE
    
Autor: Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Enero 2025
Versión: 1.0 - Migración Raspberry Pi 5
"""

import sys
import platform
import logging
import time
from typing import Any, Dict, Optional
from enum import Enum

logger = logging.getLogger(__name__)

# Estados y constantes GPIO
class GPIOMode(Enum):
    """Modos de operación GPIO."""
    SIMULATION = "simulation"
    LGPIO = "lgpio"  # Raspberry Pi 5
    RPI_GPIO = "rpi_gpio"  # Raspberry Pi < 5

class GPIOState:
    """Estados GPIO estándar."""
    LOW = 0
    HIGH = 1
    
    # Modos de pin
    IN = "in"
    OUT = "out"
    
    # Modos de numeración
    BCM = "bcm"
    BOARD = "board"
    
    # Pull up/down
    PUD_OFF = 0
    PUD_DOWN = 1  
    PUD_UP = 2

class SimulatedGPIO:
    """Simulador GPIO para desarrollo en Windows."""
    
    def __init__(self):
        self.mode = None
        self.warnings = True
        self.pins_setup = {}
        self.pin_states = {}
        self.pwm_instances = {}
        logger.info("🖥️ GPIO Simulado iniciado (modo desarrollo Windows)")
    
    def setmode(self, mode):
        """Configura el modo de numeración."""
        self.mode = mode
        logger.debug(f"GPIO: setmode({mode})")
    
    def setwarnings(self, enabled):
        """Habilita/deshabilita warnings."""
        self.warnings = enabled
        logger.debug(f"GPIO: setwarnings({enabled})")
    
    def setup(self, pin, mode, pull_up_down=GPIOState.PUD_OFF):
        """Configura un pin."""
        self.pins_setup[pin] = {"mode": mode, "pull": pull_up_down}
        self.pin_states[pin] = GPIOState.LOW
        logger.debug(f"GPIO: setup(pin={pin}, mode={mode}, pull={pull_up_down})")
    
    def output(self, pin, state):
        """Establece estado de salida de un pin."""
        if pin not in self.pins_setup:
            logger.warning(f"Pin {pin} no configurado, configurando automáticamente")
            self.setup(pin, GPIOState.OUT)
        
        self.pin_states[pin] = state
        logger.debug(f"GPIO: output(pin={pin}, state={'HIGH' if state else 'LOW'})")
    
    def input(self, pin):
        """Lee el estado de un pin."""
        if pin not in self.pins_setup:
            # Auto-configurar como entrada para evitar spam de warnings en simulación
            self.setup(pin, GPIOState.IN)
            logger.debug(f"GPIO: auto-setup(pin={pin}, mode=IN) para lectura")
        
        state = self.pin_states.get(pin, GPIOState.LOW)
        logger.debug(f"GPIO: input(pin={pin}) -> {'HIGH' if state else 'LOW'}")
        return state
    
    def PWM(self, pin, frequency):
        """Crea una instancia PWM simulada."""
        logger.debug(f"GPIO: PWM(pin={pin}, freq={frequency}Hz)")
        return SimulatedPWM(pin, frequency)
    
    def cleanup(self, pins=None):
        """Limpia la configuración GPIO."""
        if pins is None:
            self.pins_setup.clear()
            self.pin_states.clear()
            logger.debug("GPIO: cleanup(all)")
        else:
            if isinstance(pins, int):
                pins = [pins]
            for pin in pins:
                self.pins_setup.pop(pin, None)
                self.pin_states.pop(pin, None)
            logger.debug(f"GPIO: cleanup({pins})")

class SimulatedPWM:
    """Simulador PWM para desarrollo."""
    
    def __init__(self, pin, frequency):
        self.pin = pin
        self.frequency = frequency
        self.duty_cycle = 0
        self.running = False
        logger.debug(f"PWM: Creado en pin {pin} @ {frequency}Hz")
    
    def start(self, duty_cycle):
        """Inicia PWM con duty cycle inicial."""
        self.duty_cycle = duty_cycle
        self.running = True
        logger.debug(f"PWM: start(pin={self.pin}, duty={duty_cycle}%)")
    
    def ChangeDutyCycle(self, duty_cycle):
        """Cambia el duty cycle."""
        self.duty_cycle = duty_cycle
        logger.debug(f"PWM: ChangeDutyCycle(pin={self.pin}, duty={duty_cycle}%)")
    
    def ChangeFrequency(self, frequency):
        """Cambia la frecuencia."""
        self.frequency = frequency
        logger.debug(f"PWM: ChangeFrequency(pin={self.pin}, freq={frequency}Hz)")
    
    def stop(self):
        """Detiene PWM."""
        self.running = False
        logger.debug(f"PWM: stop(pin={self.pin})")

class LGPIOWrapper:
    """Wrapper para lgpio (Raspberry Pi 5)."""
    
    # Pines reservados para pigpio (servos MG995)
    # Estos pines NO deben ser reclamados por lgpio si pigpio está activo
    PIGPIO_RESERVED_PINS = {12, 13, 18}  # Servos: manzanas, peras, limones (GPIO 12/13/18 - PWM hardware)
    
    def __init__(self):
        import lgpio
        self.lgpio = lgpio
        self.chip_handle = None
        self.pins_setup = {}
        self.pwm_instances = {}
        self.mode = None
        self._alerts = {}
        self._poll_threads = {}
        self.pigpio_active = self._check_pigpio_daemon()
        
        logger.info("🍓 LGPIO iniciado (Raspberry Pi 5)")
        
        if self.pigpio_active:
            logger.warning(f"⚠️ Daemon pigpio detectado - Pines {self.PIGPIO_RESERVED_PINS} reservados para servos")
            logger.warning("   lgpio NO reclamará estos pines para evitar conflictos")
        
        # Abrir handle del chip GPIO
        try:
            self.chip_handle = self.lgpio.gpiochip_open(0)  # Chip 0 es el principal
            logger.info("✅ Chip GPIO abierto correctamente")
        except Exception as e:
            logger.error(f"❌ Error abriendo chip GPIO: {e}")
            raise
    
    def _check_pigpio_daemon(self) -> bool:
        """Verifica si el daemon pigpio está corriendo."""
        try:
            import pigpio
            pi = pigpio.pi()
            is_connected = pi.connected
            pi.stop()
            return is_connected
        except:
            return False
    
    def setmode(self, mode):
        """Configura el modo (lgpio siempre usa BCM)."""
        self.mode = mode
        if mode != GPIOState.BCM:
            logger.warning("LGPIO siempre usa numeración BCM, ignorando modo solicitado")
    
    def setwarnings(self, enabled):
        """Habilita/deshabilita warnings (no aplicable en lgpio)."""
        pass
    
    def setup(self, pin, mode, pull_up_down=GPIOState.PUD_OFF):
        """Configura un pin con reintentos si está ocupado (GPIO busy)."""
        try:
            # PROTECCIÓN: No reclamar pines reservados para pigpio
            if self.pigpio_active and pin in self.PIGPIO_RESERVED_PINS:
                logger.warning(f"⚠️ Pin {pin} reservado para pigpio - lgpio NO lo reclamará")
                logger.warning(f"   Si necesitas este pin con lgpio, detén el daemon pigpio: sudo killall pigpiod")
                # Marcar como configurado pero sin reclamar realmente
                self.pins_setup[pin] = {"mode": mode, "pull": pull_up_down, "reserved_for_pigpio": True}
                return
            
            if mode == GPIOState.OUT:
                # Configurar como salida (nivel inicial en LOW) con reintentos
                self._claim_output_with_retry(pin, initial_level=0)
            else:
                # Configurar como entrada con pull-ups/downs si aplica, con reintentos
                flags = 0
                if pull_up_down == GPIOState.PUD_UP:
                    flags = self.lgpio.SET_PULL_UP
                elif pull_up_down == GPIOState.PUD_DOWN:
                    flags = self.lgpio.SET_PULL_DOWN
                self._claim_input_with_retry(pin, flags)
            
            self.pins_setup[pin] = {"mode": mode, "pull": pull_up_down}
            logger.debug(f"LGPIO: setup(pin={pin}, mode={mode})")
            
        except Exception as e:
            logger.error(f"Error configurando pin {pin}: {e}")
            raise

    def _claim_input_with_retry(self, pin: int, flags: int, attempts: int = 3, delay_s: float = 0.05):
        """Reintenta reclamar un pin como entrada si está ocupado."""
        for attempt in range(1, max(1, attempts) + 1):
            try:
                self.lgpio.gpio_claim_input(self.chip_handle, pin, flags)
                return
            except Exception as e:
                # Reintento si el error indica ocupado
                if 'busy' in str(e).lower():
                    try:
                        # Intentar liberar por si quedó en mal estado con este handle
                        self.lgpio.gpio_free(self.chip_handle, pin)
                    except Exception:
                        pass
                    if attempt < attempts:
                        time.sleep(delay_s)
                        continue
                # Otros errores o último intento
                raise

    def _claim_output_with_retry(self, pin: int, initial_level: int = 0, attempts: int = 3, delay_s: float = 0.05):
        """Reclama un pin como salida con reintentos y nivel inicial definido."""
        level = 1 if int(initial_level) != 0 else 0
        for attempt in range(1, max(1, attempts) + 1):
            try:
                # Parámetros: handle, gpio, level, lFlags=0
                self.lgpio.gpio_claim_output(self.chip_handle, pin, level)
                return
            except Exception as e:
                if 'busy' in str(e).lower():
                    try:
                        self.lgpio.gpio_free(self.chip_handle, pin)
                    except Exception:
                        pass
                    if attempt < attempts:
                        time.sleep(delay_s)
                        continue
                raise
    
    def output(self, pin, state):
        """Establece estado de salida."""
        try:
            self.lgpio.gpio_write(self.chip_handle, pin, int(state))
            logger.debug(f"LGPIO: output(pin={pin}, state={'HIGH' if state else 'LOW'})")
        except Exception as e:
            logger.error(f"Error escribiendo pin {pin}: {e}")
    
    def input(self, pin):
        """Lee el estado de un pin."""
        try:
            state = self.lgpio.gpio_read(self.chip_handle, pin)
            logger.debug(f"LGPIO: input(pin={pin}) -> {'HIGH' if state else 'LOW'}")
            return state
        except Exception as e:
            logger.error(f"Error leyendo pin {pin}: {e}")
            return 0
    
    def PWM(self, pin, frequency):
        """Crea instancia PWM usando lgpio."""
        # PROTECCIÓN: No crear PWM en pines reservados para pigpio
        if self.pigpio_active and pin in self.PIGPIO_RESERVED_PINS:
            logger.error(f"❌ Pin {pin} reservado para pigpio - NO se puede crear PWM con lgpio")
            logger.error(f"   Detén pigpio o usa otro pin. Daemon pigpio usa estos pines.")
            # Retornar wrapper dummy que no hará nada
            return SimulatedPWM(pin, frequency)
        
        return LGPIOPWMWrapper(self.lgpio, self.chip_handle, pin, frequency)
    
    def cleanup(self, pins=None):
        """Limpia configuración GPIO."""
        try:
            if pins is None:
                # Limpiar todos los pines configurados
                pins = list(self.pins_setup.keys())
            elif isinstance(pins, int):
                pins = [pins]
            
            # Detener alertas asociadas
            for pin in list(self._alerts.keys()):
                try:
                    if pins is None or pin in pins:
                        # Quitar callback y liberar pin si fue reclamado para alertas
                        try:
                            self.lgpio.gpio_set_alert_func(self.chip_handle, pin, None)
                        except Exception:
                            pass
                        self._alerts.pop(pin, None)
                except Exception:
                    pass

            for pin in pins:
                try:
                    self.lgpio.gpio_free(self.chip_handle, pin)
                    self.pins_setup.pop(pin, None)
                except:
                    pass
            
            logger.debug(f"LGPIO: cleanup({pins if pins else 'all'})")
            
        except Exception as e:
            logger.error(f"Error en cleanup: {e}")
    
    def __del__(self):
        """Destructor - cerrar handle del chip."""
        try:
            if self.chip_handle is not None:
                self.lgpio.gpiochip_close(self.chip_handle)
                logger.debug("LGPIO: Chip GPIO cerrado")
        except:
            pass

    # --- Compatibilidad con add_event_detect/remove_event_detect ---
    def add_event_detect(self, pin, edge, callback=None, bouncetime=None):
        """Registra callback por flanco usando alertas de lgpio.
        edge: GPIO.RISING / GPIO.FALLING / GPIO.BOTH (o strings)
        bouncetime: en milisegundos (opcional)
        """
        try:
            # Determinar bandera de flanco
            edge_lower = str(edge).lower()
            if 'both' in edge_lower:
                lg_edge = self.lgpio.BOTH_EDGES
            elif 'rising' in edge_lower:
                lg_edge = self.lgpio.RISING_EDGE
            else:
                lg_edge = self.lgpio.FALLING_EDGE

            # Intentar liberar si ya estaba reclamado como input simple
            try:
                if pin in self.pins_setup:
                    self.lgpio.gpio_free(self.chip_handle, pin)
            except Exception:
                pass

            # Preparar flags de pull-up/down si estaban configurados previamente
            flags = 0
            try:
                pull = self.pins_setup.get(pin, {}).get("pull", GPIOState.PUD_OFF)
                if pull == GPIOState.PUD_UP and hasattr(self.lgpio, 'SET_PULL_UP'):
                    flags |= self.lgpio.SET_PULL_UP
                elif pull == GPIOState.PUD_DOWN and hasattr(self.lgpio, 'SET_PULL_DOWN'):
                    flags |= self.lgpio.SET_PULL_DOWN
            except Exception:
                pass

            # Reclamar pin como alerta (conservando pull si aplica)
            try:
                self.lgpio.gpio_claim_alert(self.chip_handle, pin, lg_edge, flags)
            except Exception:
                # Si falla, volver a intentar reclamando como entrada y luego alerta
                try:
                    self._claim_input_with_retry(pin, flags)
                    self.lgpio.gpio_claim_alert(self.chip_handle, pin, lg_edge, flags)
                except Exception as e2:
                    logger.warning(f"LGPIO: No se pudo reclamar alerta en pin {pin}: {e2}. Usando polling.")
                    # Como fallback, iniciar un hilo de polling que detecte flancos y llame el callback
                    self._start_polling_edge(pin, edge_lower, callback, bouncetime)
                    return

            # Debounce/glitch filter si está disponible
            try:
                if bouncetime and int(bouncetime) > 0 and hasattr(self.lgpio, 'gpio_set_debounce_micros'):
                    self.lgpio.gpio_set_debounce_micros(self.chip_handle, pin, int(bouncetime) * 1000)
            except Exception:
                pass

            # Registrar callback adaptador
            def _lg_callback(handle, gpio, level, tick):
                try:
                    if callback:
                        callback(gpio)
                except Exception as e:
                    logger.error(f"LGPIO: Error en callback de alerta pin {gpio}: {e}")

            try:
                # Algunos builds de lgpio no exponen gpio_set_alert_func; hacer fallback si no existe
                if hasattr(self.lgpio, 'gpio_set_alert_func'):
                    self.lgpio.gpio_set_alert_func(self.chip_handle, pin, _lg_callback)
                    self._alerts[pin] = _lg_callback
                    # Guardar configuración como entrada para consistencia (mantener pull)
                    existing_pull = self.pins_setup.get(pin, {}).get("pull", GPIOState.PUD_OFF)
                    self.pins_setup[pin] = {"mode": GPIOState.IN, "pull": existing_pull}
                else:
                    raise AttributeError('gpio_set_alert_func not available')
            except Exception as e:
                logger.warning(f"LGPIO: No se pudo establecer callback de alerta en pin {pin}: {e}. Usando polling.")
                try:
                    # Asegurar que el pin quede como entrada legible
                    try:
                        self._claim_input_with_retry(pin, flags)
                    except Exception:
                        pass
                    self._start_polling_edge(pin, edge_lower, callback, bouncetime)
                except Exception:
                    pass
        except Exception as e:
            logger.debug(f"LGPIO: add_event_detect fallback/polling: {e}")

    def remove_event_detect(self, pin):
        """Elimina un callback de evento previamente registrado."""
        try:
            if pin in self._alerts:
                try:
                    self.lgpio.gpio_set_alert_func(self.chip_handle, pin, None)
                except Exception:
                    pass
                self._alerts.pop(pin, None)
            # Detener polling si activo
            if pin in self._poll_threads:
                try:
                    self._poll_threads[pin]['stop'] = True
                    th = self._poll_threads[pin].get('thread')
                    if th and th.is_alive():
                        # dar tiempo a terminar
                        import time as _t
                        for _ in range(10):
                            if not th.is_alive():
                                break
                            _t.sleep(0.005)
                except Exception:
                    pass
                self._poll_threads.pop(pin, None)
            # Mantener el pin reclamado como entrada si estaba en uso
        except Exception as e:
            logger.debug(f"LGPIO: remove_event_detect ignorado para pin {pin}: {e}")

    # --- Fallback: polling por software para detección de flancos ---
    def _start_polling_edge(self, pin, edge_lower, callback, bouncetime):
        try:
            # Asegurar pin legible como entrada si no está reclamado
            try:
                self._claim_input_with_retry(pin, 0)
            except Exception:
                pass

            import threading
            import time as _time

            target_edges = edge_lower
            debounce_s = max(0.0, (int(bouncetime) if bouncetime else 0) / 1000.0)

            def _poll_loop():
                last = self.input(pin)
                last_event = 0.0
                while True:
                    if self._poll_threads.get(pin, {}).get('stop'):
                        break
                    cur = self.input(pin)
                    now = _time.time()
                    if cur != last:
                        is_rising = (last == 0 and cur == 1)
                        is_falling = (last == 1 and cur == 0)
                        match = (
                            ('both' in target_edges) or
                            ('rising' in target_edges and is_rising) or
                            ('falling' in target_edges and is_falling)
                        )
                        if match and (now - last_event) >= debounce_s:
                            try:
                                if callback:
                                    callback(pin)
                            except Exception:
                                pass
                            last_event = now
                        last = cur
                    _time.sleep(0.001)

            self._poll_threads[pin] = {'stop': False}
            th = threading.Thread(target=_poll_loop, daemon=True)
            self._poll_threads[pin]['thread'] = th
            th.start()
            # Registrar para consistencia API
            self._alerts[pin] = callback or (lambda *_: None)
        except Exception as e:
            logger.debug(f"LGPIO: error iniciando polling para pin {pin}: {e}")

class LGPIOPWMWrapper:
    """Wrapper PWM para lgpio."""
    
    def __init__(self, lgpio_module, chip_handle, pin, frequency):
        self.lgpio = lgpio_module
        self.chip_handle = chip_handle
        self.pin = pin
        self.frequency = frequency
        self.duty_cycle = 0
        self.running = False
        self.pwm_handle = None
        self.use_tx_pwm = False
        self._thread = None
        self._stop_flag = False
        self._lock = None
        
        # Configurar pin para PWM
        try:
            self.lgpio.gpio_claim_output(self.chip_handle, pin, 0)
            logger.debug(f"LGPIO PWM: Creado en pin {pin} @ {frequency}Hz")
        except Exception as e:
            logger.error(f"Error configurando PWM en pin {pin}: {e}")
    
    def start(self, duty_cycle):
        """Inicia PWM."""
        try:
            # Calcular parámetros PWM
            self.duty_cycle = duty_cycle
            
            # Intentar usar tx_pwm si está disponible
            try:
                if hasattr(self.lgpio, 'tx_pwm'):
                    # lgpio.tx_pwm espera duty en [0.0, 1.0]
                    duty_0_1 = max(0.0, min(1.0, float(self.duty_cycle) / 100.0))
                    self.lgpio.tx_pwm(self.chip_handle, self.pin, int(self.frequency), duty_0_1)
                    self.use_tx_pwm = True
                    self.running = True
                    logger.debug(f"LGPIO PWM (tx_pwm): start(pin={self.pin}, freq={self.frequency}Hz, duty={duty_cycle}%)")
                    return
            except Exception as e:
                logger.debug(f"LGPIO tx_pwm no disponible/usable, usando PWM por software: {e}")
                self.use_tx_pwm = False
            
            # Fallback: PWM por software con hilo dedicado
            self._software_pwm_start(duty_cycle)
            self.running = True
            logger.debug(f"LGPIO PWM (soft): start(pin={self.pin}, freq={self.frequency}Hz, duty={duty_cycle}%)")
            
        except Exception as e:
            logger.error(f"Error iniciando PWM: {e}")
    
    def ChangeDutyCycle(self, duty_cycle):
        """Cambia duty cycle."""
        self.duty_cycle = duty_cycle
        try:
            if self.running:
                if self.use_tx_pwm and hasattr(self.lgpio, 'tx_pwm'):
                    # Convertir de porcentaje [0-100] a rango [0.0-1.0] requerido por lgpio.tx_pwm
                    duty_0_1 = max(0.0, min(1.0, float(self.duty_cycle) / 100.0))
                    self.lgpio.tx_pwm(self.chip_handle, self.pin, int(self.frequency), duty_0_1)
                else:
                    self._software_pwm_update(duty_cycle)
            logger.debug(f"LGPIO PWM: ChangeDutyCycle(pin={self.pin}, duty={duty_cycle}%)")
        except Exception as e:
            logger.error(f"Error cambiando duty cycle: {e}")
    
    def ChangeFrequency(self, frequency):
        """Cambia frecuencia."""
        self.frequency = frequency
        logger.debug(f"LGPIO PWM: ChangeFrequency(pin={self.pin}, freq={frequency}Hz)")
    
    def stop(self):
        """Detiene PWM."""
        try:
            if not self.running:
                return
            if self.use_tx_pwm and hasattr(self.lgpio, 'tx_pwm'):
                try:
                    # duty 0 para detener salida
                    self.lgpio.tx_pwm(self.chip_handle, self.pin, int(self.frequency), 0.0)
                except Exception:
                    pass
            else:
                # Detener hilo de PWM por software
                try:
                    self._stop_flag = True
                    if self._thread and self._thread.is_alive():
                        # Dar tiempo a que finalice el ciclo
                        import time as _t
                        for _ in range(50):
                            if not self._thread.is_alive():
                                break
                            _t.sleep(0.005)
                except Exception:
                    pass
            # Asegurar salida en bajo
            try:
                self.lgpio.gpio_write(self.chip_handle, self.pin, 0)
            except Exception:
                pass
            self.running = False
            logger.debug(f"LGPIO PWM: stop(pin={self.pin})")
        except Exception as e:
            logger.error(f"Error deteniendo PWM: {e}")
    
    def _soft_pwm_loop(self):
        """Bucle de PWM por software (precisión limitada)."""
        try:
            import time as _time
            while not self._stop_flag:
                # Evitar división por cero
                freq = max(1.0, float(self.frequency))
                period = 1.0 / freq
                duty = max(0.0, min(100.0, float(self.duty_cycle)))
                high_time = (duty / 100.0) * period
                low_time = period - high_time
                # Alto
                try:
                    self.lgpio.gpio_write(self.chip_handle, self.pin, 1 if duty > 0 else 0)
                except Exception:
                    pass
                if high_time > 0:
                    _time.sleep(high_time)
                # Bajo
                try:
                    self.lgpio.gpio_write(self.chip_handle, self.pin, 0)
                except Exception:
                    pass
                if low_time > 0:
                    _time.sleep(low_time)
        except Exception as e:
            logger.debug(f"LGPIO PWM soft loop terminado: {e}")

    def _software_pwm_start(self, duty_cycle):
        """Inicia PWM por software con hilo dedicado."""
        try:
            self._stop_flag = False
            import threading as _threading
            self._thread = _threading.Thread(target=self._soft_pwm_loop, daemon=True)
            self._thread.start()
        except Exception as e:
            logger.error(f"Error iniciando PWM por software: {e}")
    
    def _software_pwm_update(self, duty_cycle):
        """Actualiza parámetros del PWM por software (se aplican en siguiente ciclo)."""
        # No se requiere acción inmediata; el hilo lee self.duty_cycle y self.frequency continuamente

# Detección automática del entorno y carga del wrapper apropiado
def _detect_and_load_gpio():
    """Detecta el entorno y carga el wrapper GPIO apropiado."""
    
    # 1. Detectar sistema operativo
    if sys.platform == 'win32':
        logger.info("🖥️ Entorno Windows detectado - Usando simulador GPIO")
        return SimulatedGPIO(), GPIOMode.SIMULATION
    
    # 2. Detectar si estamos en Raspberry Pi
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
            
        if 'Raspberry Pi' in cpuinfo:
            logger.info("🍓 Raspberry Pi detectado")
            
            # 3. Detectar versión de Raspberry Pi
            if 'BCM2712' in cpuinfo or 'bcm2712' in cpuinfo:  # Raspberry Pi 5 (robusto)
                logger.info("🚀 Raspberry Pi 5 detectado - Usando LGPIO")
                try:
                    return LGPIOWrapper(), GPIOMode.LGPIO
                except ImportError:
                    logger.error("❌ lgpio no disponible. Instalar con: sudo apt install python3-lgpio")
                    raise
            else:
                # Si no se detectó explícitamente Pi 5, intentar usar lgpio si está disponible
                try:
                    import lgpio  # noqa: F401
                    logger.info("🧪 lgpio disponible - usándolo como backend GPIO")
                    return LGPIOWrapper(), GPIOMode.LGPIO
                except Exception:
                    pass
                # Raspberry Pi < 5 - usar RPi.GPIO como fallback
                logger.info("📟 Raspberry Pi < 5 detectado - Usando RPi.GPIO")
                try:
                    import RPi.GPIO as GPIO_module
                    return GPIO_module, GPIOMode.RPI_GPIO
                except ImportError:
                    logger.warning("RPi.GPIO no disponible, usando simulador")
                    return SimulatedGPIO(), GPIOMode.SIMULATION
        else:
            logger.info("🐧 Sistema Linux no-Raspberry Pi detectado - Usando simulador")
            return SimulatedGPIO(), GPIOMode.SIMULATION
            
    except FileNotFoundError:
        logger.info("📋 /proc/cpuinfo no encontrado - Usando simulador GPIO")
        return SimulatedGPIO(), GPIOMode.SIMULATION

# Cargar wrapper GPIO apropiado
try:
    GPIO, GPIO_MODE = _detect_and_load_gpio()
    GPIO_AVAILABLE = True
    
    # Añadir constantes al objeto GPIO si no las tiene
    if not hasattr(GPIO, 'LOW'):
        GPIO.LOW = GPIOState.LOW
        GPIO.HIGH = GPIOState.HIGH
        GPIO.IN = GPIOState.IN
        GPIO.OUT = GPIOState.OUT
        GPIO.BCM = GPIOState.BCM
        GPIO.BOARD = GPIOState.BOARD
        GPIO.PUD_OFF = GPIOState.PUD_OFF
        GPIO.PUD_UP = GPIOState.PUD_UP
        GPIO.PUD_DOWN = GPIOState.PUD_DOWN
    
    logger.info(f"✅ GPIO wrapper cargado: {GPIO_MODE.value}")
    
except Exception as e:
    logger.error(f"❌ Error cargando GPIO wrapper: {e}")
    GPIO = SimulatedGPIO()
    GPIO_MODE = GPIOMode.SIMULATION
    GPIO_AVAILABLE = False

# Funciones de utilidad
def get_gpio_info():
    """Retorna información sobre el sistema GPIO actual."""
    return {
        "mode": GPIO_MODE.value,
        "available": GPIO_AVAILABLE,
        "platform": sys.platform,
        "gpio_type": type(GPIO).__name__
    }

def is_simulation_mode():
    """Verifica si estamos en modo simulación."""
    return GPIO_MODE == GPIOMode.SIMULATION

def is_raspberry_pi5():
    """Verifica si estamos en Raspberry Pi 5."""
    return GPIO_MODE == GPIOMode.LGPIO

# Exportar para uso externo
__all__ = [
    'GPIO', 'GPIO_AVAILABLE', 'GPIO_MODE', 'GPIOState', 'GPIOMode',
    'get_gpio_info', 'is_simulation_mode', 'is_raspberry_pi5'
]

if __name__ == "__main__":
    # Test del wrapper
    info = get_gpio_info()
    print(f"GPIO Info: {info}")
    
    # Test básico
    print("Probando GPIO wrapper...")
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(18, GPIO.OUT)
    GPIO.output(18, GPIO.HIGH)
    print("Test HIGH")
    time.sleep(0.5)
    GPIO.output(18, GPIO.LOW)
    print("Test LOW")
    GPIO.cleanup()
    print("✅ Test completado")
