#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Prueba de Conexión - VisiFruit
=========================================

Prueba la conexión entre Raspberry Pi y servidor de IA.
Verifica latencia, autenticación y rendimiento.

Uso:
    python test_connection.py
"""

import asyncio
import time
import sys
import json
from pathlib import Path
import numpy as np
import cv2

# Colores ANSI
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}{NC}\n")

def print_success(text):
    print(f"{GREEN}✓ {text}{NC}")

def print_error(text):
    print(f"{RED}✗ {text}{NC}")

def print_warning(text):
    print(f"{YELLOW}⚠ {text}{NC}")

def print_info(text):
    print(f"  {text}")


async def test_async_client():
    """Prueba el cliente asíncrono."""
    try:
        from IA_Etiquetado.async_inference_client import AsyncInferenceClient
    except ImportError:
        print_error("No se puede importar AsyncInferenceClient")
        print_info("Asegúrate de estar en el directorio correcto")
        return False
    
    print_header("PRUEBA DE CLIENTE ASÍNCRONO")
    
    # Cargar configuración
    try:
        config_path = Path("Prototipo_Clasificador/Config_Prototipo.json")
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        remote_cfg = config.get("remote_inference", {})
        
        print_info(f"Servidor: {remote_cfg.get('server_url')}")
        print_info(f"Token configurado: {'Sí' if remote_cfg.get('auth_token') else 'No'}")
        print()
        
    except Exception as e:
        print_error(f"Error cargando configuración: {e}")
        return False
    
    # Configurar cliente
    try:
        client_config = {
            "server_url": remote_cfg.get("server_url", "http://localhost:9000"),
            "auth_token": remote_cfg.get("auth_token"),
            "timeouts": {
                "connect": remote_cfg.get("connect_timeout_s", 0.5),
                "read": remote_cfg.get("read_timeout_s", 1.0),
                "write": remote_cfg.get("write_timeout_s", 1.0),
                "pool": remote_cfg.get("pool_timeout_s", 0.5)
            },
            "compression": {
                "jpeg_quality": remote_cfg.get("jpeg_quality", 85),
                "max_dimension": remote_cfg.get("max_dimension", 640),
                "auto_quality": remote_cfg.get("auto_quality", True)
            },
            "circuit_breaker": {
                "failure_threshold": remote_cfg.get("cb_failure_threshold", 3),
                "timeout_seconds": remote_cfg.get("cb_timeout_seconds", 20.0),
                "half_open_requests": remote_cfg.get("cb_half_open_requests", 1)
            }
        }
        
        client = AsyncInferenceClient(client_config)
        print_success("Cliente asíncrono creado")
        
    except Exception as e:
        print_error(f"Error creando cliente: {e}")
        return False
    
    # Prueba 1: Health Check
    print_info("\n[1/3] Probando health check...")
    try:
        start = time.time()
        healthy = await client.health()
        latency = (time.time() - start) * 1000
        
        if healthy:
            print_success(f"Health check exitoso ({latency:.1f}ms)")
        else:
            print_error("Health check falló - servidor no responde")
            return False
            
    except Exception as e:
        print_error(f"Error en health check: {e}")
        return False
    
    # Prueba 2: Inferencia con imagen sintética
    print_info("\n[2/3] Probando inferencia con imagen sintética...")
    try:
        # Crear imagen de prueba
        test_image = np.random.randint(0, 255, (640, 480, 3), dtype=np.uint8)
        
        params = {
            "input_size": 640,
            "confidence_threshold": 0.5,
            "iou_threshold": 0.45,
            "max_detections": 100,
            "class_names": ["apple", "pear", "lemon"]
        }
        
        start = time.time()
        result = await client.infer(test_image, params)
        latency = (time.time() - start) * 1000
        
        if result:
            print_success(f"Inferencia exitosa ({latency:.1f}ms)")
            
            detections = result.get("detections", [])
            print_info(f"   Detecciones: {len(detections)}")
            
            if "client_metadata" in result:
                metadata = result["client_metadata"]
                print_info(f"   Compresión: {metadata.get('compression', {}).get('size_bytes', 0)} bytes")
            
        else:
            print_error("Inferencia falló - sin resultado")
            return False
            
    except Exception as e:
        print_error(f"Error en inferencia: {e}")
        return False
    
    # Prueba 3: Benchmark de latencia
    print_info("\n[3/3] Realizando benchmark de latencia (10 iteraciones)...")
    try:
        latencies = []
        
        for i in range(10):
            start = time.time()
            result = await client.infer(test_image, params)
            latency = (time.time() - start) * 1000
            latencies.append(latency)
            print_info(f"   Iteración {i+1}: {latency:.1f}ms")
        
        avg_latency = sum(latencies) / len(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)
        
        print()
        print_success(f"Benchmark completado:")
        print_info(f"   Promedio: {avg_latency:.1f}ms")
        print_info(f"   Mínimo: {min_latency:.1f}ms")
        print_info(f"   Máximo: {max_latency:.1f}ms")
        
        # Evaluación del rendimiento
        print()
        if avg_latency < 300:
            print_success("Rendimiento EXCELENTE (<300ms)")
        elif avg_latency < 500:
            print_success("Rendimiento BUENO (<500ms)")
        elif avg_latency < 800:
            print_warning("Rendimiento ACEPTABLE (<800ms)")
        else:
            print_warning("Rendimiento BAJO (>800ms) - considera optimizar")
        
    except Exception as e:
        print_error(f"Error en benchmark: {e}")
        return False
    
    # Obtener estadísticas del cliente
    print_info("\n[ESTADÍSTICAS DEL CLIENTE]")
    try:
        stats = client.get_stats()
        print_info(f"   Peticiones totales: {stats.get('requests_total', 0)}")
        print_info(f"   Peticiones exitosas: {stats.get('requests_success', 0)}")
        print_info(f"   Peticiones fallidas: {stats.get('requests_failed', 0)}")
        print_info(f"   Tasa de éxito: {stats.get('success_rate', 0)*100:.1f}%")
        print_info(f"   Circuit breaker: {stats.get('circuit_breaker_state', 'unknown')}")
        
    except Exception as e:
        print_warning(f"No se pudieron obtener estadísticas: {e}")
    
    # Cerrar cliente
    await client.close()
    
    return True


async def test_network():
    """Prueba conectividad de red básica."""
    print_header("PRUEBA DE RED")
    
    try:
        config_path = Path("Prototipo_Clasificador/Config_Prototipo.json")
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        remote_cfg = config.get("remote_inference", {})
        server_url = remote_cfg.get("server_url", "http://localhost:9000")
        
        # Extraer host del URL
        import re
        match = re.search(r'://([^:/]+)', server_url)
        if match:
            host = match.group(1)
        else:
            host = "localhost"
        
        print_info(f"Host del servidor: {host}")
        print()
        
        # Ping test (solo en sistemas Unix)
        import platform
        import subprocess
        
        if platform.system() != "Windows":
            print_info("Probando conectividad con ping...")
            try:
                result = subprocess.run(
                    ["ping", "-c", "3", host],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode == 0:
                    print_success("Ping exitoso")
                else:
                    print_warning("Ping falló - pero HTTP aún puede funcionar")
            except Exception as e:
                print_warning(f"No se pudo hacer ping: {e}")
        else:
            print_info("(Prueba de ping omitida en Windows)")
        
        return True
        
    except Exception as e:
        print_error(f"Error en prueba de red: {e}")
        return False


async def main():
    """Función principal."""
    print(f"\n{BLUE}{'='*60}")
    print("  VisiFruit - Prueba de Conexión")
    print("  Cliente Asíncrono HTTP/2")
    print(f"{'='*60}{NC}\n")
    
    # Verificar que estamos en el directorio correcto
    if not Path("Prototipo_Clasificador/Config_Prototipo.json").exists():
        print_error("No se encuentra Config_Prototipo.json")
        print_info("Ejecuta este script desde el directorio raíz de VisiFruit")
        sys.exit(1)
    
    # Verificar dependencias
    try:
        import httpx
        print_success("httpx instalado")
    except ImportError:
        print_error("httpx no está instalado")
        print_info("Instala con: pip install httpx[http2]")
        sys.exit(1)
    
    # Ejecutar pruebas
    success = True
    
    # Prueba de red
    if not await test_network():
        success = False
    
    # Prueba de cliente asíncrono
    if not await test_async_client():
        success = False
    
    # Resultado final
    print_header("RESULTADO FINAL")
    
    if success:
        print_success("TODAS LAS PRUEBAS EXITOSAS ✓")
        print_info("Tu sistema está listo para funcionar")
        print()
        print_info("Siguiente paso:")
        print_info("  1. Inicia el servidor: python ai_inference_server.py")
        print_info("  2. Inicia el clasificador: python Prototipo_Clasificador/smart_classifier_system.py")
    else:
        print_error("ALGUNAS PRUEBAS FALLARON ✗")
        print_info("Revisa los errores anteriores")
        print()
        print_info("Soluciones comunes:")
        print_info("  - Asegúrate de que el servidor está corriendo")
        print_info("  - Verifica la configuración en Config_Prototipo.json")
        print_info("  - Revisa que el puerto 9000 esté abierto en el firewall")
        print_info("  - Confirma que el token coincide en servidor y cliente")
    
    print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Prueba interrumpida por el usuario{NC}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{RED}Error fatal: {e}{NC}")
        sys.exit(1)
