#!/usr/bin/env python3
"""
VisiFruit Launcher Simple - Sin GUI
==================================

Launcher de línea de comandos que funciona sin tkinter.
Ideal para cuando hay problemas con Tcl/Tk.
"""

import subprocess
import sys
import time
import webbrowser
from pathlib import Path
import requests

def check_port(port):
    """Verifica si un puerto está en uso"""
    try:
        response = requests.get(f"http://localhost:{port}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def show_status():
    """Muestra el estado actual de los servicios"""
    print("\n" + "="*50)
    print("📊 ESTADO DEL SISTEMA VISIFRUIT")
    print("="*50)
    
    services = [
        ("Backend", 8001),
        ("Frontend", 3000), 
        ("Sistema Principal", 8000)
    ]
    
    for name, port in services:
        status = "🟢 FUNCIONANDO" if check_port(port) else "🔴 DETENIDO"
        print(f"{name:20} (Puerto {port}): {status}")
    
    print("="*50)

def start_complete_system():
    """Inicia el sistema completo"""
    print("🚀 Iniciando sistema completo...")
    
    if not Path("main_etiquetadora.py").exists():
        print("❌ Error: No se encuentra main_etiquetadora.py")
        print("   Ejecuta desde la raíz del proyecto VisiFruit")
        return
    
    # Ejecutar script de inicio
    if Path("start_sistema_completo.ps1").exists():
        script = "start_sistema_completo.ps1"
        subprocess.Popen(["powershell", "-ExecutionPolicy", "Bypass", "-File", script])
    elif Path("start_sistema_completo.bat").exists():
        script = "start_sistema_completo.bat"
        subprocess.Popen([script])
    else:
        print("❌ No se encontró script de inicio")
        return
    
    print("✅ Sistema iniciado")
    print("⏳ Esperando 8 segundos para abrir navegador...")
    time.sleep(8)
    
    try:
        webbrowser.open("http://localhost:3000")
        print("🌐 Navegador abierto en http://localhost:3000")
    except:
        print("⚠️ No se pudo abrir navegador automáticamente")

def stop_services():
    """Detiene todos los servicios"""
    print("⏹️ Deteniendo servicios...")
    
    ports = [8000, 8001, 3000]
    for port in ports:
        try:
            subprocess.run([
                "powershell", "-Command",
                f"Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | ForEach-Object {{ Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }}"
            ], capture_output=True)
        except:
            pass
    
    print("✅ Servicios detenidos")

def start_individual_service(service_name, script_name):
    """Inicia un servicio individual"""
    print(f"🔧 Iniciando {service_name}...")
    
    if Path(script_name).exists():
        subprocess.Popen([script_name], creationflags=subprocess.CREATE_NEW_CONSOLE)
        print(f"✅ {service_name} iniciado")
    else:
        print(f"❌ No se encontró {script_name}")

def open_urls():
    """Abre URLs importantes en el navegador"""
    urls = [
        ("Frontend", "http://localhost:3000"),
        ("Backend API", "http://localhost:8001/api/docs"),
        ("Sistema Principal", "http://localhost:8000")
    ]
    
    print("\n🔗 Abriendo URLs:")
    for name, url in urls:
        try:
            webbrowser.open(url)
            print(f"   🌐 {name}: {url}")
            time.sleep(1)  # Evitar abrir todo al mismo tiempo
        except:
            print(f"   ❌ Error abriendo {name}")

def main_menu():
    """Menú principal"""
    while True:
        print("\n" + "="*50)
        print("🍎 VISIFRUIT LAUNCHER SIMPLE")
        print("="*50)
        print("1. 🚀 Iniciar Sistema Completo")
        print("2. 📊 Ver Estado de Servicios")
        print("3. ⏹️ Detener Todos los Servicios")
        print("4. 🔧 Iniciar Backend")
        print("5. 💻 Iniciar Frontend")
        print("6. 🏭 Iniciar Sistema Principal")
        print("7. 🌐 Abrir URLs en Navegador")
        print("8. ❌ Salir")
        print("="*50)
        
        try:
            choice = input("Elige una opción (1-8): ").strip()
            
            if choice == "1":
                start_complete_system()
            elif choice == "2":
                show_status()
            elif choice == "3":
                stop_services()
            elif choice == "4":
                start_individual_service("Backend", "start_backend.bat")
            elif choice == "5":
                start_individual_service("Frontend", "start_frontend.bat")
            elif choice == "6":
                start_individual_service("Sistema Principal", "main_etiquetadora.py")
            elif choice == "7":
                open_urls()
            elif choice == "8":
                print("👋 ¡Hasta luego!")
                break
            else:
                print("❌ Opción no válida")
        
        except KeyboardInterrupt:
            print("\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🍎 VisiFruit Launcher Simple v1.0")
    print("Launcher sin GUI - Funciona sin tkinter")
    main_menu()
