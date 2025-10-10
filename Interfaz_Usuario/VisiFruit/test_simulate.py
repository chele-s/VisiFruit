#!/usr/bin/env python3
"""
Script de prueba para simular detecciones en el frontend
=========================================================

Este script envía peticiones POST a /api/system/simulate del backend (8001)
para simular detecciones de frutas y verificar que el frontend las muestre
en tiempo real.

Uso:
    python test_simulate.py [--url URL] [--count COUNT] [--interval SECONDS]
    
Ejemplo:
    python test_simulate.py --count 10 --interval 2
"""

import requests
import time
import argparse
import sys
from datetime import datetime


def simulate_detection(url: str) -> dict:
    """
    Envía una petición de simulación al backend.
    
    Args:
        url: URL del endpoint de simulación
        
    Returns:
        Respuesta JSON del backend
    """
    try:
        response = requests.post(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error en la petición: {e}")
        return {"error": str(e)}


def main():
    parser = argparse.ArgumentParser(
        description="Simula detecciones de frutas para testing del frontend"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8001/api/system/simulate",
        help="URL del endpoint de simulación (default: http://localhost:8001/api/system/simulate)"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=5,
        help="Número de simulaciones a ejecutar (default: 5)"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=3.0,
        help="Intervalo en segundos entre simulaciones (default: 3.0)"
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🧪 TEST DE SIMULACIÓN DE DETECCIONES - VISIFRUIT")
    print("=" * 70)
    print(f"URL: {args.url}")
    print(f"Simulaciones: {args.count}")
    print(f"Intervalo: {args.interval}s")
    print("=" * 70)
    print()
    
    # Verificar conexión al backend
    print("🔍 Verificando conexión al backend...")
    try:
        health_url = args.url.replace("/api/system/simulate", "/health")
        response = requests.get(health_url, timeout=5)
        if response.status_code == 200:
            print("✅ Backend conectado correctamente")
            health = response.json()
            print(f"   Estado: {health.get('status', 'unknown')}")
            print(f"   Uptime: {health.get('uptime_seconds', 0):.1f}s")
        else:
            print(f"⚠️ Backend respondió con código {response.status_code}")
    except Exception as e:
        print(f"❌ No se pudo conectar al backend: {e}")
        print("   Asegúrate de que el backend esté corriendo en el puerto 8001")
        sys.exit(1)
    
    print()
    print("🚀 Iniciando simulaciones...")
    print()
    
    success_count = 0
    error_count = 0
    
    for i in range(1, args.count + 1):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] Simulación {i}/{args.count}...", end=" ")
        
        result = simulate_detection(args.url)
        
        if "error" in result:
            print(f"❌ Error")
            error_count += 1
        else:
            print(f"✅ OK")
            success_count += 1
            
            # Mostrar resumen de detecciones
            if "detections" in result:
                detections = result["detections"]
                print(f"   └─ Detectadas: {len(detections)} frutas")
                
                # Mostrar categorías detectadas
                categories = {}
                for detection in detections:
                    cat = detection.get("category", "unknown")
                    categories[cat] = categories.get(cat, 0) + 1
                
                for cat, count in categories.items():
                    emoji_map = {
                        "apple": "🍎",
                        "pear": "🍐", 
                        "lemon": "🍋",
                        "orange": "🍊",
                        "banana": "🍌"
                    }
                    emoji = emoji_map.get(cat, "🍏")
                    print(f"      {emoji} {cat}: {count}")
        
        # Esperar antes de la siguiente simulación (excepto la última)
        if i < args.count:
            time.sleep(args.interval)
    
    print()
    print("=" * 70)
    print("📊 RESUMEN")
    print("=" * 70)
    print(f"Total ejecutadas: {args.count}")
    print(f"Exitosas: {success_count} ✅")
    print(f"Errores: {error_count} ❌")
    print(f"Tasa de éxito: {(success_count/args.count)*100:.1f}%")
    print("=" * 70)
    print()
    print("💡 SIGUIENTE PASO:")
    print("   1. Abre el frontend en http://localhost:5173")
    print("   2. Ve a la vista de 'Producción'")
    print("   3. Verifica que veas las actualizaciones en tiempo real:")
    print("      - Categoría Activa debe cambiar")
    print("      - Última Detección debe aparecer")
    print("      - El emoji debe pulsar cuando hay detecciones")
    print()


if __name__ == "__main__":
    main()
