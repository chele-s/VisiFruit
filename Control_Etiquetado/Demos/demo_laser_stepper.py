#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo: Laser YK0008 + DRV8825 Stepper
------------------------------------
Inicializa el sensor láser y el stepper, y activa el stepper cada vez
que se detecta el objeto (trigger). Útil para validar el hardware del
aplicador vertical de la etiquetadora.
"""
import asyncio
import json
import time
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from Control_Etiquetado.sensor_interface import SensorInterface
from Control_Etiquetado.labeler_actuator import LabelerActuator


async def main():
    # Cargar configuración base si existe; si no, usar defaults razonables
    cfg_path = Path("Config_Etiquetadora.json")
    if cfg_path.exists():
        config = json.loads(cfg_path.read_text(encoding="utf-8"))
        sensor_cfg = config.get("sensor_settings", {})
        stepper_cfg = config.get("laser_stepper_settings", {})
    else:
        sensor_cfg = {
            "trigger_sensor": {
                "type": "laser_yk0008",
                "name": "LaserYK0008",
                "pin_bcm": 17,
                "trigger_level": "falling",
                "debounce_time_ms": 30,
                "pull_up_down": "PUD_UP",
            }
        }
        stepper_cfg = {
            "type": "stepper",
            "name": "LabelApplicatorStepper",
            "step_pin_bcm": 19,
            "dir_pin_bcm": 26,
            "enable_pin_bcm": 21,
            "enable_active_low": True,
            "base_speed_sps": 1500,
            "step_pulse_us": 4,
        }

    # Crear stepper
    stepper_cfg = dict(stepper_cfg)
    stepper_cfg["type"] = "stepper"
    stepper = LabelerActuator(stepper_cfg)
    assert await stepper.initialize(), "No se pudo inicializar el stepper"

    # Crear sensor interface
    sensor = SensorInterface()
    assert sensor.initialize(sensor_cfg), "No se pudo inicializar SensorInterface"
    sensor.enable_trigger_monitoring()

    last_activation = 0.0
    min_interval = (
        stepper_cfg.get("activation_on_laser", {})
        .get("min_interval_seconds", 0.15)
    )
    duration = (
        stepper_cfg.get("activation_on_laser", {})
        .get("activation_duration_seconds", 0.6)
    )
    intensity = (
        stepper_cfg.get("activation_on_laser", {})
        .get("intensity_percent", 80.0)
    )

    print("\n=== Demo Laser + Stepper ===")
    print("Rompe el haz del láser para activar el stepper...")

    try:
        while True:
            if sensor.check_trigger_state():
                now = time.time()
                if now - last_activation >= min_interval:
                    last_activation = now
                    print("Laser detectado → activando stepper...")
                    await stepper.activate_for_duration(duration, intensity)
                await asyncio.sleep(0.01)
            else:
                await asyncio.sleep(0.01)
    except KeyboardInterrupt:
        print("\nSaliendo demo...")
    finally:
        try:
            sensor.shutdown()
        except Exception:
            pass
        await stepper.cleanup()


if __name__ == "__main__":
    asyncio.run(main())


