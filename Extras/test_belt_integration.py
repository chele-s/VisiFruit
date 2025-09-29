#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 Script de Verificación de Integración - Control de Banda
============================================================

Verifica que todos los endpoints necesarios para el frontend
estén funcionando correctamente en ambos sistemas:
- Sistema Principal (puerto 8000)
- Sistema Demo (puerto 8002)

Uso:
    python Extras/test_belt_integration.py
    
    # O con URLs personalizadas:
    python Extras/test_belt_integration.py --main http://192.168.1.100:8000 --demo http://192.168.1.100:8002
"""

import asyncio
import aiohttp
import sys
import argparse
from typing import Dict, List, Tuple
from datetime import datetime
import json

# ANSI color codes para terminal
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text: str):
    """Imprime un encabezado formateado."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text:^70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}\n")

def print_success(text: str):
    """Imprime mensaje de éxito."""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text: str):
    """Imprime mensaje de error."""
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_warning(text: str):
    """Imprime mensaje de advertencia."""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_info(text: str):
    """Imprime mensaje informativo."""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")

# Definir endpoints a verificar
BELT_ENDPOINTS = [
    ("POST", "/belt/start_forward", None, "Iniciar banda hacia adelante"),
    ("POST", "/belt/start_backward", None, "Iniciar banda hacia atrás"),
    ("POST", "/belt/stop", None, "Detener banda"),
    ("POST", "/belt/emergency_stop", None, "Parada de emergencia"),
    ("POST", "/belt/set_speed", {"speed": 1.0}, "Establecer velocidad"),
    ("POST", "/belt/toggle_enable", None, "Alternar habilitación"),
    ("GET", "/belt/status", None, "Obtener estado de banda"),
]

STEPPER_ENDPOINTS = [
    ("POST", "/laser_stepper/toggle", {"enabled": True}, "Habilitar/Deshabilitar stepper"),
    ("POST", "/laser_stepper/test", {"duration": 0.3, "intensity": 50.0}, "Probar stepper (demo corto)"),
]

HEALTH_ENDPOINT = ("GET", "/health", None, "Health check")

async def test_endpoint(
    session: aiohttp.ClientSession,
    base_url: str,
    method: str,
    endpoint: str,
    body: Dict = None,
    description: str = ""
) -> Tuple[bool, str, Dict]:
    """
    Prueba un endpoint específico.
    
    Returns:
        Tuple[bool, str, Dict]: (success, message, response_data)
    """
    url = f"{base_url}{endpoint}"
    
    try:
        # Configurar timeout
        timeout = aiohttp.ClientTimeout(total=10)
        
        # Hacer la petición
        if method == "GET":
            async with session.get(url, timeout=timeout) as response:
                data = await response.json()
                success = response.status in [200, 201]
        else:  # POST
            headers = {"Content-Type": "application/json"}
            json_body = json.dumps(body) if body else None
            async with session.post(url, data=json_body, headers=headers, timeout=timeout) as response:
                data = await response.json()
                success = response.status in [200, 201]
        
        if success:
            return True, f"{description}: OK", data
        else:
            return False, f"{description}: HTTP {response.status}", data
            
    except aiohttp.ClientConnectorError:
        return False, f"{description}: No se pudo conectar al servidor", {}
    except asyncio.TimeoutError:
        return False, f"{description}: Timeout (>10s)", {}
    except json.JSONDecodeError:
        return False, f"{description}: Respuesta no es JSON válido", {}
    except Exception as e:
        return False, f"{description}: {type(e).__name__}: {str(e)}", {}

async def test_system(base_url: str, system_name: str) -> Tuple[int, int]:
    """
    Prueba todos los endpoints de un sistema.
    
    Returns:
        Tuple[int, int]: (passed_count, total_count)
    """
    print_header(f"Probando: {system_name}")
    print_info(f"URL Base: {base_url}")
    
    async with aiohttp.ClientSession() as session:
        passed = 0
        total = 0
        
        # 1. Health check
        print(f"\n{Colors.BOLD}1️⃣  Health Check{Colors.END}")
        method, endpoint, body, desc = HEALTH_ENDPOINT
        success, message, data = await test_endpoint(session, base_url, method, endpoint, body, desc)
        total += 1
        if success:
            passed += 1
            print_success(message)
            if "status" in data:
                print_info(f"   Status: {data['status']}")
            if "version" in data:
                print_info(f"   Version: {data['version']}")
        else:
            print_error(message)
        
        # 2. Belt endpoints
        print(f"\n{Colors.BOLD}2️⃣  Endpoints de Control de Banda{Colors.END}")
        for method, endpoint, body, desc in BELT_ENDPOINTS:
            success, message, data = await test_endpoint(session, base_url, method, endpoint, body, desc)
            total += 1
            if success:
                passed += 1
                print_success(f"{endpoint}: {desc}")
                # Mostrar información adicional relevante
                if "message" in data:
                    print_info(f"   → {data['message']}")
            else:
                print_error(f"{endpoint}: {message}")
        
        # 3. Stepper endpoints
        print(f"\n{Colors.BOLD}3️⃣  Endpoints de Motor Stepper (NEMA 17){Colors.END}")
        for method, endpoint, body, desc in STEPPER_ENDPOINTS:
            success, message, data = await test_endpoint(session, base_url, method, endpoint, body, desc)
            total += 1
            if success:
                passed += 1
                print_success(f"{endpoint}: {desc}")
                if "message" in data:
                    print_info(f"   → {data['message']}")
                if "simulation" in data and data["simulation"]:
                    print_warning(f"   → Modo simulación (hardware no disponible)")
            else:
                print_error(f"{endpoint}: {message}")
        
        # Resumen
        print(f"\n{Colors.BOLD}📊 Resumen de {system_name}{Colors.END}")
        success_rate = (passed / total * 100) if total > 0 else 0
        
        if success_rate == 100:
            print_success(f"Todos los tests pasaron: {passed}/{total} ({success_rate:.1f}%)")
        elif success_rate >= 70:
            print_warning(f"Algunos tests fallaron: {passed}/{total} ({success_rate:.1f}%)")
        else:
            print_error(f"Muchos tests fallaron: {passed}/{total} ({success_rate:.1f}%)")
        
        return passed, total

async def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Verifica la integración del control de banda con el frontend"
    )
    parser.add_argument(
        '--main',
        default='http://localhost:8000',
        help='URL del sistema principal (default: http://localhost:8000)'
    )
    parser.add_argument(
        '--demo',
        default='http://localhost:8002',
        help='URL del sistema demo (default: http://localhost:8002)'
    )
    parser.add_argument(
        '--skip-main',
        action='store_true',
        help='Omitir pruebas del sistema principal'
    )
    parser.add_argument(
        '--skip-demo',
        action='store_true',
        help='Omitir pruebas del sistema demo'
    )
    
    args = parser.parse_args()
    
    print_header("🧪 Test de Integración - Control de Banda VisiFruit")
    print_info(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    total_passed = 0
    total_tests = 0
    
    # Probar sistema principal
    if not args.skip_main:
        passed, total = await test_system(args.main, "Sistema Principal")
        total_passed += passed
        total_tests += total
        await asyncio.sleep(1)  # Pausa entre sistemas
    
    # Probar sistema demo
    if not args.skip_demo:
        passed, total = await test_system(args.demo, "Sistema Demo")
        total_passed += passed
        total_tests += total
    
    # Resumen final
    print_header("📈 RESUMEN FINAL")
    overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    print(f"Total de pruebas ejecutadas: {Colors.BOLD}{total_tests}{Colors.END}")
    print(f"Pruebas exitosas: {Colors.GREEN}{Colors.BOLD}{total_passed}{Colors.END}")
    print(f"Pruebas fallidas: {Colors.RED}{Colors.BOLD}{total_tests - total_passed}{Colors.END}")
    print(f"Tasa de éxito: {Colors.BOLD}{overall_success_rate:.1f}%{Colors.END}")
    
    if overall_success_rate == 100:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ¡PERFECTO! Todos los sistemas están funcionando correctamente.{Colors.END}")
        print_info("Tu frontend puede conectarse sin problemas a ambos sistemas.")
        return 0
    elif overall_success_rate >= 70:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  ADVERTENCIA: Algunos endpoints no funcionan.{Colors.END}")
        print_warning("Revisa los errores anteriores y asegúrate de que los servicios estén ejecutándose.")
        return 1
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ ERROR: Muchos tests fallaron.{Colors.END}")
        print_error("Verifica que los servicios estén ejecutándose:")
        print_info("  Terminal 1: python main_etiquetadora_v4.py")
        print_info("  Terminal 2: python Control_Etiquetado/demo_sistema_web_server.py")
        return 2

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⚠️  Tests interrumpidos por el usuario.{Colors.END}")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n{Colors.RED}❌ Error inesperado: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
