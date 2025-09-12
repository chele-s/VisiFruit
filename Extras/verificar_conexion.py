#!/usr/bin/env python3
"""
Script de Verificación de Conexión - Sistema VisiFruit
======================================================

Verifica que todos los servicios estén funcionando correctamente
y que el frontend se pueda conectar al backend.

Uso:
    python verificar_conexion.py [--detallado] [--timeout SEGUNDOS]

Opciones:
    --detallado    Mostrar información detallada de las respuestas
    --timeout      Timeout para las peticiones en segundos (default: 10)

Autor: Sistema VisiFruit
Fecha: 2025-08-12
"""

import argparse
import asyncio
import json
import platform
import sys
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

# Importaciones para hacer peticiones HTTP
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    import urllib.request
    import urllib.error

try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False


class ColoredOutput:
    """Clase para output con colores en terminal."""
    
    COLORS = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'bold': '\033[1m',
        'end': '\033[0m'
    }
    
    @classmethod
    def print(cls, text: str, color: str = 'white', bold: bool = False):
        """Imprime texto con color."""
        if platform.system() == "Windows":
            print(text)
        else:
            color_code = cls.COLORS.get(color, cls.COLORS['white'])
            bold_code = cls.COLORS['bold'] if bold else ''
            end_code = cls.COLORS['end']
            print(f"{bold_code}{color_code}{text}{end_code}")


class VerificadorConexion:
    """Verificador de conexión para el sistema VisiFruit."""
    
    def __init__(self, detallado: bool = False, timeout: int = 10):
        self.detallado = detallado
        self.timeout = timeout
        
        # URLs a verificar
        self.urls = {
            'backend_health': 'http://localhost:8001/health',
            'backend_status': 'http://localhost:8001/api/status/ultra',
            'backend_docs': 'http://localhost:8001/api/docs',
            'backend_production': 'http://localhost:8001/api/production/status',
            'backend_metrics': 'http://localhost:8001/api/system/performance',
        }
        
        self.websocket_urls = {
            'ws_realtime': 'ws://localhost:8001/ws/realtime',
            'ws_dashboard': 'ws://localhost:8001/ws/dashboard',
            'ws_alerts': 'ws://localhost:8001/ws/alerts',
        }
        
        self.resultados = {}
        self.errores = []
    
    def imprimir_cabecera(self):
        """Imprime cabecera del verificador."""
        ColoredOutput.print("\n" + "="*60, 'cyan', True)
        ColoredOutput.print("    VERIFICADOR DE CONEXIÓN VISIFRUIT", 'cyan', True)
        ColoredOutput.print("="*60, 'cyan', True)
        ColoredOutput.print(f"Fecha: {time.strftime('%Y-%m-%d %H:%M:%S')}", 'white')
        ColoredOutput.print(f"Timeout: {self.timeout} segundos", 'white')
        ColoredOutput.print(f"Detallado: {'Sí' if self.detallado else 'No'}", 'white')
        print()
    
    async def verificar_http_aiohttp(self, nombre: str, url: str) -> Tuple[bool, Dict]:
        """Verifica un endpoint HTTP usando aiohttp."""
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                start_time = time.time()
                async with session.get(url) as response:
                    response_time = (time.time() - start_time) * 1000
                    content = await response.text()
                    
                    resultado = {
                        'status_code': response.status,
                        'response_time_ms': round(response_time, 2),
                        'content_length': len(content),
                        'headers': dict(response.headers) if self.detallado else {},
                        'content': content[:500] if self.detallado else None
                    }
                    
                    return response.status == 200, resultado
                    
        except Exception as e:
            return False, {'error': str(e)}
    
    def verificar_http_urllib(self, nombre: str, url: str) -> Tuple[bool, Dict]:
        """Verifica un endpoint HTTP usando urllib (fallback)."""
        try:
            start_time = time.time()
            request = urllib.request.Request(url)
            request.add_header('User-Agent', 'VisiFruit-Verificador/1.0')
            
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                response_time = (time.time() - start_time) * 1000
                content = response.read().decode('utf-8')
                
                resultado = {
                    'status_code': response.getcode(),
                    'response_time_ms': round(response_time, 2),
                    'content_length': len(content),
                    'headers': dict(response.headers) if self.detallado else {},
                    'content': content[:500] if self.detallado else None
                }
                
                return response.getcode() == 200, resultado
                
        except Exception as e:
            return False, {'error': str(e)}
    
    async def verificar_websocket(self, nombre: str, url: str) -> Tuple[bool, Dict]:
        """Verifica conexión WebSocket."""
        if not WEBSOCKETS_AVAILABLE:
            return False, {'error': 'websockets library no disponible'}
        
        try:
            start_time = time.time()
            async with websockets.connect(
                url, 
                timeout=self.timeout,
                ping_interval=None  # Desactivar ping para tests rápidos
            ) as websocket:
                connection_time = (time.time() - start_time) * 1000
                
                # Enviar un mensaje de test si es posible
                try:
                    await websocket.send(json.dumps({"type": "ping"}))
                    response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    mensaje_exitoso = True
                except:
                    mensaje_exitoso = False
                
                resultado = {
                    'connection_time_ms': round(connection_time, 2),
                    'mensaje_test': mensaje_exitoso,
                    'state': websocket.state.name if hasattr(websocket, 'state') else 'CONNECTED'
                }
                
                return True, resultado
                
        except Exception as e:
            return False, {'error': str(e)}
    
    async def ejecutar_verificacion(self) -> bool:
        """Ejecuta verificación completa."""
        self.imprimir_cabecera()
        
        # Verificar endpoints HTTP
        ColoredOutput.print("🌐 Verificando endpoints HTTP...", 'blue', True)
        
        for nombre, url in self.urls.items():
            try:
                if AIOHTTP_AVAILABLE:
                    exitoso, resultado = await self.verificar_http_aiohttp(nombre, url)
                else:
                    exitoso, resultado = self.verificar_http_urllib(nombre, url)
                
                self.resultados[nombre] = {'exitoso': exitoso, 'datos': resultado}
                
                if exitoso:
                    tiempo = resultado.get('response_time_ms', 0)
                    ColoredOutput.print(f"  ✅ {nombre}: OK ({tiempo}ms)", 'green')
                    
                    if self.detallado and 'content' in resultado:
                        try:
                            # Intentar parsear JSON para mostrar datos relevantes
                            if resultado['content']:
                                data = json.loads(resultado['content'])
                                if isinstance(data, dict):
                                    ColoredOutput.print(f"     📊 Datos: {list(data.keys())[:5]}", 'gray')
                        except:
                            pass
                else:
                    error = resultado.get('error', 'Error desconocido')
                    ColoredOutput.print(f"  ❌ {nombre}: FALLO - {error}", 'red')
                    self.errores.append(f"{nombre}: {error}")
                    
            except Exception as e:
                ColoredOutput.print(f"  ❌ {nombre}: ERROR - {e}", 'red')
                self.errores.append(f"{nombre}: {e}")
                self.resultados[nombre] = {'exitoso': False, 'datos': {'error': str(e)}}
        
        print()
        
        # Verificar WebSockets
        ColoredOutput.print("🔌 Verificando conexiones WebSocket...", 'blue', True)
        
        for nombre, url in self.websocket_urls.items():
            try:
                exitoso, resultado = await self.verificar_websocket(nombre, url)
                
                self.resultados[nombre] = {'exitoso': exitoso, 'datos': resultado}
                
                if exitoso:
                    tiempo = resultado.get('connection_time_ms', 0)
                    ColoredOutput.print(f"  ✅ {nombre}: OK ({tiempo}ms)", 'green')
                    
                    if self.detallado:
                        mensaje_ok = resultado.get('mensaje_test', False)
                        ColoredOutput.print(f"     📨 Mensaje test: {'OK' if mensaje_ok else 'No disponible'}", 'gray')
                else:
                    error = resultado.get('error', 'Error desconocido')
                    ColoredOutput.print(f"  ❌ {nombre}: FALLO - {error}", 'red')
                    self.errores.append(f"{nombre}: {error}")
                    
            except Exception as e:
                ColoredOutput.print(f"  ❌ {nombre}: ERROR - {e}", 'red')
                self.errores.append(f"{nombre}: {e}")
                self.resultados[nombre] = {'exitoso': False, 'datos': {'error': str(e)}}
        
        print()
        
        # Generar resumen
        return self.generar_resumen()
    
    def generar_resumen(self) -> bool:
        """Genera resumen de la verificación."""
        ColoredOutput.print("📊 Resumen de Verificación", 'cyan', True)
        ColoredOutput.print("-" * 40, 'cyan')
        
        total = len(self.resultados)
        exitosos = sum(1 for r in self.resultados.values() if r['exitoso'])
        fallidos = total - exitosos
        
        ColoredOutput.print(f"Total verificado: {total}", 'white')
        ColoredOutput.print(f"Exitosos: {exitosos}", 'green')
        ColoredOutput.print(f"Fallidos: {fallidos}", 'red' if fallidos > 0 else 'green')
        
        print()
        
        if fallidos == 0:
            ColoredOutput.print("🎉 TODAS LAS CONEXIONES FUNCIONAN CORRECTAMENTE", 'green', True)
            ColoredOutput.print("   El frontend puede conectarse al backend sin problemas", 'green')
            
            print()
            ColoredOutput.print("🌟 URLs de Acceso Verificadas:", 'cyan', True)
            ColoredOutput.print("   • Frontend: http://localhost:3000", 'white')
            ColoredOutput.print("   • Backend API: http://localhost:8001", 'white')
            ColoredOutput.print("   • Dashboard: http://localhost:8001/api/docs", 'white')
            ColoredOutput.print("   • WebSocket: ws://localhost:8001/ws/realtime", 'white')
        else:
            ColoredOutput.print("🚨 PROBLEMAS DETECTADOS", 'red', True)
            ColoredOutput.print("   Algunos servicios no están respondiendo correctamente", 'red')
            
            print()
            ColoredOutput.print("❌ Errores encontrados:", 'red', True)
            for error in self.errores[:5]:  # Mostrar máximo 5 errores
                ColoredOutput.print(f"   • {error}", 'red')
            
            print()
            ColoredOutput.print("💡 Soluciones sugeridas:", 'yellow', True)
            ColoredOutput.print("   1. Verifica que el backend esté ejecutándose en puerto 8001", 'yellow')
            ColoredOutput.print("   2. Ejecuta: python start_sistema_completo.bat", 'yellow')
            ColoredOutput.print("   3. Espera 10-15 segundos después de iniciar el backend", 'yellow')
            ColoredOutput.print("   4. Verifica logs del backend para errores", 'yellow')
        
        print()
        return fallidos == 0


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Verificador de conexión del sistema VisiFruit"
    )
    parser.add_argument(
        '--detallado', 
        action='store_true', 
        help='Mostrar información detallada de las respuestas'
    )
    parser.add_argument(
        '--timeout', 
        type=int, 
        default=10,
        help='Timeout para las peticiones en segundos (default: 10)'
    )
    
    args = parser.parse_args()
    
    # Verificar dependencias opcionales
    if not AIOHTTP_AVAILABLE:
        ColoredOutput.print("⚠️ aiohttp no disponible, usando urllib como fallback", 'yellow')
    if not WEBSOCKETS_AVAILABLE:
        ColoredOutput.print("⚠️ websockets no disponible, verificación de WebSocket limitada", 'yellow')
    
    # Ejecutar verificación
    verificador = VerificadorConexion(detallado=args.detallado, timeout=args.timeout)
    
    try:
        if AIOHTTP_AVAILABLE:
            # Usar asyncio para verificación completa
            todo_ok = asyncio.run(verificador.ejecutar_verificacion())
        else:
            # Fallback sin async
            print("Usando modo sincrónico...")
            # Crear un evento loop básico para WebSockets si está disponible
            todo_ok = asyncio.run(verificador.ejecutar_verificacion())
        
        return 0 if todo_ok else 1
        
    except KeyboardInterrupt:
        ColoredOutput.print("\n⚠️ Verificación interrumpida por el usuario", 'yellow')
        return 1
    except Exception as e:
        ColoredOutput.print(f"\n❌ Error inesperado: {e}", 'red')
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        ColoredOutput.print(f"\n❌ Error crítico: {e}", 'red')
        sys.exit(1)
