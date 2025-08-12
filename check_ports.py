#!/usr/bin/env python3
"""
Script para verificar el estado de los puertos del sistema VisiFruit
=====================================================================

Verifica qué puertos están ocupados y por qué procesos,
para ayudar a diagnosticar conflictos antes de iniciar servicios.

Uso:
    python check_ports.py

Autor: Sistema VisiFruit
Fecha: $(Get-Date -Format "yyyy-MM-dd")
"""

import socket
import sys
import subprocess
import platform
from typing import Dict, List, Optional, Tuple


def check_port(host: str, port: int) -> bool:
    """Verifica si un puerto está ocupado."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            return result == 0
    except Exception:
        return False


def get_process_using_port(port: int) -> Optional[str]:
    """Obtiene información del proceso que usa un puerto específico."""
    try:
        if platform.system() == "Windows":
            # Windows
            cmd = f"netstat -ano | findstr :{port}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0 and result.stdout:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if f":{port}" in line and "LISTENING" in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            pid = parts[-1]
                            # Obtener nombre del proceso
                            try:
                                tasklist_cmd = f"tasklist /FI \"PID eq {pid}\" /FO CSV /NH"
                                tasklist_result = subprocess.run(tasklist_cmd, shell=True, capture_output=True, text=True)
                                if tasklist_result.returncode == 0 and tasklist_result.stdout:
                                    process_line = tasklist_result.stdout.strip().split(',')[0].strip('"')
                                    return f"PID {pid} ({process_line})"
                            except Exception:
                                return f"PID {pid}"
        else:
            # Linux/macOS
            cmd = f"lsof -i :{port}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0 and result.stdout:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                if lines:
                    parts = lines[0].split()
                    return f"{parts[0]} (PID {parts[1]})"
    except Exception as e:
        return f"Error: {e}"
    
    return None


def main():
    """Función principal."""
    print("🔌 Verificador de Puertos - Sistema VisiFruit")
    print("=" * 50)
    print()
    
    # Definir puertos críticos del sistema
    critical_ports = {
        8000: "Sistema Principal (main_etiquetadora.py)",
        8001: "Backend Adicional (Backend/main.py)",
        3000: "Frontend React (desarrollo)",
        5173: "Frontend React (Vite)"
    }
    
    all_clear = True
    occupied_ports = []
    
    print("Verificando puertos críticos...")
    print("-" * 30)
    
    for port, description in critical_ports.items():
        is_occupied = check_port("localhost", port)
        status = "🔴 OCUPADO" if is_occupied else "🟢 LIBRE"
        
        print(f"Puerto {port:4d}: {status:10s} - {description}")
        
        if is_occupied:
            all_clear = False
            occupied_ports.append(port)
            process_info = get_process_using_port(port)
            if process_info:
                print(f"              Usado por: {process_info}")
    
    print()
    print("=" * 50)
    
    if all_clear:
        print("✅ Todos los puertos críticos están disponibles")
        print("🚀 Puedes iniciar los servicios sin problemas")
    else:
        print(f"⚠️  {len(occupied_ports)} puerto(s) ocupado(s): {occupied_ports}")
        print()
        print("💡 Soluciones sugeridas:")
        
        for port in occupied_ports:
            if port == 8000:
                print(f"   • Puerto {port}: Detener servicio anterior o cambiar puerto en Config_Etiquetadora.json")
            elif port == 8001:
                print(f"   • Puerto {port}: Detener backend anterior o cambiar puerto en Backend/main.py")
            elif port in [3000, 5173]:
                print(f"   • Puerto {port}: Detener servidor React anterior (Ctrl+C)")
        
        print()
        print("🔧 Para terminar procesos en Windows:")
        print("   netstat -ano | findstr :<puerto>")
        print("   taskkill /PID <PID> /F")
    
    print()
    return 0 if all_clear else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupción por usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
