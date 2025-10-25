#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

try:
    from Control_Etiquetado.relay_motor_controller_pi5 import create_relay_motor_driver_pi5
    USE_PI5 = True
except Exception:
    from Control_Etiquetado.relay_motor_controller import create_relay_motor_driver
    USE_PI5 = False


async def main():
    relay1_pin = 18  # Adelante
    relay2_pin = 19  # Atrás
    enable_pin = 26  # Enable (opcional)

    if USE_PI5:
        driver = create_relay_motor_driver_pi5(
            relay1_pin=relay1_pin,
            relay2_pin=relay2_pin,
            enable_pin=enable_pin,
        )
    else:
        driver = create_relay_motor_driver(
            relay1_pin=relay1_pin,
            relay2_pin=relay2_pin,
            enable_pin=enable_pin,
        )

    try:
        if not await driver.initialize():
            print("No se pudo inicializar el driver de relays")
            return

        print("Activando motor hacia ADELANTE por 5s...")
        await driver.start_belt()
        await asyncio.sleep(5)
        print("Parando motor...")
        await driver.stop_belt()
    finally:
        try:
            await driver.cleanup()
        except Exception:
            pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Interrumpido por usuario")

