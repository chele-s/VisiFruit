#!/usr/bin/env python3
"""
VisiFruit Launcher Fixed - Versión compatible con Python 3.13
==============================================================

Launcher con manejo mejorado de errores de Tcl/Tk en Python 3.13.
Incluye fallbacks y configuración automática de variables de entorno.
"""

import os
import sys
import subprocess
import threading
import time
import webbrowser
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import requests

# Configurar variables de entorno para Tcl/Tk ANTES de importar tkinter
def setup_tcl_tk():
    """Configura variables de entorno para Tcl/Tk"""
    python_root = Path(sys.executable).parent
    
    # Posibles ubicaciones de Tcl/Tk
    tcl_paths = [
        python_root / "tcl" / "tcl8.6",
        python_root / "Lib" / "tcl8.6", 
        python_root / "libs" / "tcl8.6",
        python_root / "tcl",
    ]
    
    tk_paths = [
        python_root / "tcl" / "tk8.6",
        python_root / "Lib" / "tk8.6",
        python_root / "libs" / "tk8.6", 
        python_root / "tk",
    ]
    
    # Configurar TCL_LIBRARY
    for path in tcl_paths:
        if path.exists():
            os.environ["TCL_LIBRARY"] = str(path)
            break
    
    # Configurar TK_LIBRARY  
    for path in tk_paths:
        if path.exists():
            os.environ["TK_LIBRARY"] = str(path)
            break

# Configurar antes de importar tkinter
setup_tcl_tk()

# Intentar importar GUI con manejo de errores
GUI_AVAILABLE = False
CTK_AVAILABLE = False

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, scrolledtext
    GUI_AVAILABLE = True
    print("✅ Tkinter cargado correctamente")
    
    # Intentar CustomTkinter
    try:
        import customtkinter as ctk
        CTK_AVAILABLE = True
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        print("✅ CustomTkinter cargado correctamente")
    except ImportError:
        print("⚠️ CustomTkinter no disponible, usando tkinter estándar")
        
except Exception as e:
    print(f"❌ Error cargando GUI: {e}")
    print("🔄 Cambiando a modo de línea de comandos...")
    GUI_AVAILABLE = False

class ModernButton:
    """Botón moderno compatible"""
    
    def __init__(self, parent, text="", command=None, color="blue", **kwargs):
        if GUI_AVAILABLE:
            if CTK_AVAILABLE:
                self.button = ctk.CTkButton(parent, text=text, command=command, **kwargs)
            else:
                self.button = tk.Button(
                    parent, text=text, command=command,
                    bg="#1f538d" if color == "blue" else "#d32f2f" if color == "red" else "#388e3c",
                    fg="white", font=("Arial", 10, "bold"), relief="flat", bd=0,
                    padx=20, pady=10, **kwargs
                )
        else:
            # Fallback para línea de comandos
            self.button = None
            self.command = command
            self.text = text
    
    def pack(self, **kwargs):
        if self.button:
            self.button.pack(**kwargs)
    
    def grid(self, **kwargs):
        if self.button:
            self.button.grid(**kwargs)
    
    def configure(self, **kwargs):
        if self.button:
            self.button.configure(**kwargs)

class VisiFruitLauncherFixed:
    """Launcher con compatibilidad mejorada para Python 3.13"""
    
    def __init__(self):
        self.root_path = Path.cwd()
        self.backend_process = None
        self.frontend_process = None
        self.system_process = None
        self.monitoring_thread = None
        self.is_monitoring = False
        
        self.system_status = {
            "backend": "stopped",
            "frontend": "stopped", 
            "system": "stopped",
            "ports": {"8001": False, "3000": False, "8000": False}
        }
        
        if GUI_AVAILABLE:
            self.create_gui()
        else:
            self.run_cli()

    def create_gui(self):
        """Crea interfaz gráfica"""
        try:
            if CTK_AVAILABLE:
                self.root = ctk.CTk()
                self.root.title("🍎 VisiFruit Launcher v1.0 (Fixed)")
                self.root.geometry("1000x700")
            else:
                self.root = tk.Tk()
                self.root.title("🍎 VisiFruit Launcher v1.0 (Fixed)")
                self.root.geometry("1000x700")
                self.root.configure(bg="#2b2b2b")
            
            self.setup_gui_interface()
            self.start_monitoring()
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            
        except Exception as e:
            print(f"❌ Error creando GUI: {e}")
            print("🔄 Cambiando a modo línea de comandos...")
            self.run_cli()

    def setup_gui_interface(self):
        """Configura la interfaz gráfica completa"""
        # Frame principal
        if CTK_AVAILABLE:
            main_frame = ctk.CTkFrame(self.root)
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        else:
            main_frame = tk.Frame(self.root, bg="#2b2b2b")
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        self.create_header(main_frame)
        
        # Panel de control
        self.create_control_panel(main_frame)
        
        # Panel de estado
        self.create_status_panel(main_frame)
        
        # Panel de logs
        self.create_logs_panel(main_frame)
        
        # Panel de enlaces
        self.create_links_panel(main_frame)
        
        # Log inicial
        self.add_log("🚀 VisiFruit Launcher Fixed iniciado correctamente", "success")

    def create_header(self, parent):
        """Crea header"""
        if CTK_AVAILABLE:
            header = ctk.CTkFrame(parent)
            header.pack(fill="x", pady=(0, 20))
            
            title = ctk.CTkLabel(header, text="🍎 VisiFruit System Launcher (Fixed)", 
                               font=ctk.CTkFont(size=28, weight="bold"))
            title.pack(pady=20)
            
            subtitle = ctk.CTkLabel(header, text="Compatible con Python 3.13 - Sistema Industrial v3.0",
                                  font=ctk.CTkFont(size=14))
            subtitle.pack(pady=(0, 10))
        else:
            header = tk.Frame(parent, bg="#2b2b2b")
            header.pack(fill="x", pady=(0, 20))
            
            title = tk.Label(header, text="🍎 VisiFruit System Launcher (Fixed)",
                           font=("Arial", 24, "bold"), bg="#2b2b2b", fg="white")
            title.pack(pady=20)
            
            subtitle = tk.Label(header, text="Compatible con Python 3.13 - Sistema Industrial v3.0",
                              font=("Arial", 12), bg="#2b2b2b", fg="#cccccc")
            subtitle.pack()

    def create_control_panel(self, parent):
        """Crea panel de control"""
        if CTK_AVAILABLE:
            control_frame = ctk.CTkFrame(parent)
            control_frame.pack(fill="x", pady=(0, 20))
            
            title = ctk.CTkLabel(control_frame, text="🎮 Control del Sistema",
                               font=ctk.CTkFont(size=18, weight="bold"))
            title.pack(pady=(15, 10))
        else:
            control_frame = tk.LabelFrame(parent, text="🎮 Control del Sistema",
                                        font=("Arial", 14, "bold"), bg="#2b2b2b", fg="white")
            control_frame.pack(fill="x", pady=(0, 20), padx=10)
        
        # Botones principales
        if CTK_AVAILABLE:
            buttons_frame = ctk.CTkFrame(control_frame)
            buttons_frame.pack(pady=15, padx=15)
        else:
            buttons_frame = tk.Frame(control_frame, bg="#2b2b2b")
            buttons_frame.pack(pady=15)
        
        self.start_all_btn = ModernButton(buttons_frame, text="🚀 Iniciar Sistema Completo",
                                         command=self.start_complete_system, color="blue")
        self.start_all_btn.pack(side="left", padx=10)
        
        self.stop_all_btn = ModernButton(buttons_frame, text="⏹️ Detener Todo",
                                        command=self.stop_all_services, color="red")
        self.stop_all_btn.pack(side="left", padx=10)

    def create_status_panel(self, parent):
        """Crea panel de estado"""
        if CTK_AVAILABLE:
            status_frame = ctk.CTkFrame(parent)
            status_frame.pack(fill="x", pady=(0, 20))
            
            title = ctk.CTkLabel(status_frame, text="📊 Estado del Sistema",
                               font=ctk.CTkFont(size=18, weight="bold"))
            title.pack(pady=(15, 10))
        else:
            status_frame = tk.LabelFrame(parent, text="📊 Estado del Sistema",
                                       font=("Arial", 14, "bold"), bg="#2b2b2b", fg="white")
            status_frame.pack(fill="x", pady=(0, 20), padx=10)
        
        # Indicadores de estado
        if CTK_AVAILABLE:
            indicators_frame = ctk.CTkFrame(status_frame)
            indicators_frame.pack(pady=15, padx=15, fill="x")
        else:
            indicators_frame = tk.Frame(status_frame, bg="#2b2b2b")
            indicators_frame.pack(pady=15, fill="x")
        
        self.status_labels = {}
        services = [("Backend (8001)", "backend"), ("Frontend (3000)", "frontend"), ("Sistema (8000)", "system")]
        
        for i, (name, key) in enumerate(services):
            if CTK_AVAILABLE:
                frame = ctk.CTkFrame(indicators_frame)
                frame.grid(row=0, column=i, padx=10, pady=5, sticky="ew")
                
                label = ctk.CTkLabel(frame, text=name)
                label.pack(pady=(10, 5))
                
                self.status_labels[key] = ctk.CTkLabel(frame, text="●", 
                                                     font=ctk.CTkFont(size=20), text_color="red")
                self.status_labels[key].pack(pady=(0, 10))
            else:
                frame = tk.Frame(indicators_frame, bg="#3b3b3b", relief="raised", bd=1)
                frame.grid(row=0, column=i, padx=10, pady=5, sticky="ew")
                
                label = tk.Label(frame, text=name, bg="#3b3b3b", fg="white", font=("Arial", 10))
                label.pack(pady=(10, 5))
                
                self.status_labels[key] = tk.Label(frame, text="●", bg="#3b3b3b", 
                                                  fg="red", font=("Arial", 20))
                self.status_labels[key].pack(pady=(0, 10))
        
        # Configurar grid
        indicators_frame.grid_columnconfigure(0, weight=1)
        indicators_frame.grid_columnconfigure(1, weight=1)
        indicators_frame.grid_columnconfigure(2, weight=1)

    def create_logs_panel(self, parent):
        """Crea panel de logs"""
        if CTK_AVAILABLE:
            logs_frame = ctk.CTkFrame(parent)
            logs_frame.pack(fill="both", expand=True, pady=(0, 20))
            
            title = ctk.CTkLabel(logs_frame, text="📝 Registro de Actividad",
                               font=ctk.CTkFont(size=18, weight="bold"))
            title.pack(pady=(15, 10))
            
            self.logs_text = ctk.CTkTextbox(logs_frame, height=200,
                                          font=ctk.CTkFont(family="Consolas", size=11))
            self.logs_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        else:
            logs_frame = tk.LabelFrame(parent, text="📝 Registro de Actividad",
                                     font=("Arial", 14, "bold"), bg="#2b2b2b", fg="white")
            logs_frame.pack(fill="both", expand=True, pady=(0, 20), padx=10)
            
            self.logs_text = scrolledtext.ScrolledText(logs_frame, height=12, bg="#1e1e1e", 
                                                     fg="#ffffff", font=("Consolas", 10))
            self.logs_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def create_links_panel(self, parent):
        """Crea panel de enlaces"""
        if CTK_AVAILABLE:
            links_frame = ctk.CTkFrame(parent)
            links_frame.pack(fill="x")
            
            title = ctk.CTkLabel(links_frame, text="🔗 Enlaces Rápidos",
                               font=ctk.CTkFont(size=18, weight="bold"))
            title.pack(pady=(15, 10))
        else:
            links_frame = tk.LabelFrame(parent, text="🔗 Enlaces Rápidos",
                                      font=("Arial", 14, "bold"), bg="#2b2b2b", fg="white")
            links_frame.pack(fill="x", padx=10)
        
        if CTK_AVAILABLE:
            buttons_frame = ctk.CTkFrame(links_frame)
            buttons_frame.pack(pady=15, padx=15)
        else:
            buttons_frame = tk.Frame(links_frame, bg="#2b2b2b")
            buttons_frame.pack(pady=15)
        
        links = [
            ("🌐 Frontend", "http://localhost:3000"),
            ("🔧 Backend API", "http://localhost:8001/api/docs"),
            ("🏭 Sistema Principal", "http://localhost:8000")
        ]
        
        for text, url in links:
            btn = ModernButton(buttons_frame, text=text, command=lambda u=url: self.open_url(u))
            btn.pack(side="left", padx=5)

    def add_log(self, message: str, level: str = "info"):
        """Añade log con formato"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        emojis = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌", "debug": "🔍"}
        emoji = emojis.get(level, "📝")
        formatted_message = f"[{timestamp}] {emoji} {message}\n"
        
        if GUI_AVAILABLE and hasattr(self, 'logs_text'):
            if CTK_AVAILABLE:
                self.logs_text.insert("end", formatted_message)
            else:
                colors = {"info": "#ffffff", "success": "#4caf50", "warning": "#ff9800", 
                         "error": "#f44336", "debug": "#2196f3"}
                color = colors.get(level, "#ffffff")
                tag_name = f"color_{level}"
                self.logs_text.tag_configure(tag_name, foreground=color)
                self.logs_text.insert(tk.END, formatted_message, tag_name)
                self.logs_text.see(tk.END)
        else:
            print(formatted_message.strip())

    def check_ports(self) -> Dict[str, bool]:
        """Verifica puertos"""
        ports_status = {}
        for port in [8000, 8001, 3000]:
            try:
                response = requests.get(f"http://localhost:{port}/health", timeout=2)
                ports_status[str(port)] = response.status_code == 200
            except:
                ports_status[str(port)] = False
        return ports_status

    def update_status_indicators(self):
        """Actualiza indicadores"""
        self.system_status["ports"] = self.check_ports()
        
        if GUI_AVAILABLE and hasattr(self, 'status_labels'):
            for service, label in self.status_labels.items():
                port_map = {"backend": "8001", "frontend": "3000", "system": "8000"}
                port = port_map.get(service)
                
                if port and self.system_status["ports"].get(port, False):
                    color = "green"
                    self.system_status[service] = "running"
                else:
                    color = "red"
                    self.system_status[service] = "stopped"
                
                if CTK_AVAILABLE:
                    label.configure(text_color=color)
                else:
                    label.configure(fg=color)

    def start_monitoring(self):
        """Inicia monitoreo"""
        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
        self.monitoring_thread.start()

    def monitoring_loop(self):
        """Bucle de monitoreo"""
        while self.is_monitoring:
            try:
                self.update_status_indicators()
                time.sleep(3)
            except Exception as e:
                print(f"Error en monitoreo: {e}")
                time.sleep(5)

    def start_complete_system(self):
        """Inicia sistema completo"""
        self.add_log("🚀 Iniciando sistema completo...", "info")
        
        try:
            if not Path("main_etiquetadora.py").exists():
                self.add_log("❌ Error: No se encuentra main_etiquetadora.py", "error")
                return
            
            if sys.platform == "win32":
                script_path = "start_sistema_completo.ps1"
                if Path(script_path).exists():
                    subprocess.Popen(["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path])
                else:
                    script_path = "start_sistema_completo.bat"
                    subprocess.Popen([script_path])
            
            self.add_log("✅ Sistema completo iniciado", "success")
            threading.Timer(8.0, self.open_frontend_browser).start()
            
        except Exception as e:
            self.add_log(f"❌ Error iniciando sistema: {e}", "error")

    def open_frontend_browser(self):
        """Abre navegador"""
        try:
            webbrowser.open("http://localhost:3000")
            self.add_log("🌐 Frontend abierto en navegador", "success")
        except Exception as e:
            self.add_log(f"⚠️ No se pudo abrir navegador: {e}", "warning")

    def stop_all_services(self):
        """Detiene servicios"""
        self.add_log("⏹️ Deteniendo todos los servicios...", "warning")
        
        try:
            if sys.platform == "win32":
                for port in [8000, 8001, 3000]:
                    try:
                        subprocess.run([
                            "powershell", "-Command",
                            f"Get-NetTCPConnection -LocalPort {port} | ForEach-Object {{ Stop-Process -Id $_.OwningProcess -Force }}"
                        ], capture_output=True)
                    except:
                        pass
            
            self.add_log("✅ Servicios detenidos", "success")
            
        except Exception as e:
            self.add_log(f"❌ Error deteniendo servicios: {e}", "error")

    def open_url(self, url: str):
        """Abre URL"""
        try:
            webbrowser.open(url)
            self.add_log(f"🌐 Abierto: {url}", "info")
        except Exception as e:
            self.add_log(f"❌ Error abriendo URL: {e}", "error")

    def on_closing(self):
        """Maneja cierre"""
        if GUI_AVAILABLE:
            if messagebox.askokcancel("Salir", "¿Estás seguro de que quieres cerrar el launcher?"):
                self.is_monitoring = False
                self.add_log("👋 Cerrando VisiFruit Launcher...", "info")
                self.root.destroy()
        else:
            self.is_monitoring = False

    def run_cli(self):
        """Ejecuta versión CLI"""
        print("\n🍎 VisiFruit Launcher Fixed (Modo CLI)")
        print("GUI no disponible, usando línea de comandos...")
        
        while True:
            print("\n" + "="*50)
            print("OPCIONES:")
            print("1. 🚀 Iniciar Sistema Completo")
            print("2. 📊 Ver Estado")
            print("3. ⏹️ Detener Servicios")
            print("4. 🌐 Abrir URLs")
            print("5. ❌ Salir")
            print("="*50)
            
            try:
                choice = input("Elige (1-5): ").strip()
                
                if choice == "1":
                    self.start_complete_system()
                elif choice == "2":
                    self.show_cli_status()
                elif choice == "3":
                    self.stop_all_services()
                elif choice == "4":
                    self.open_all_urls()
                elif choice == "5":
                    print("👋 ¡Hasta luego!")
                    break
                else:
                    print("❌ Opción no válida")
            
            except KeyboardInterrupt:
                print("\n👋 ¡Hasta luego!")
                break

    def show_cli_status(self):
        """Muestra estado en CLI"""
        print("\n📊 ESTADO DEL SISTEMA:")
        ports = self.check_ports()
        services = [("Backend", "8001"), ("Frontend", "3000"), ("Sistema", "8000")]
        
        for name, port in services:
            status = "🟢 FUNCIONANDO" if ports.get(port, False) else "🔴 DETENIDO"
            print(f"  {name:15} (Puerto {port}): {status}")

    def open_all_urls(self):
        """Abre todas las URLs"""
        urls = [
            ("Frontend", "http://localhost:3000"),
            ("Backend API", "http://localhost:8001/api/docs"),
            ("Sistema Principal", "http://localhost:8000")
        ]
        
        for name, url in urls:
            try:
                webbrowser.open(url)
                print(f"🌐 Abierto: {name} ({url})")
                time.sleep(1)
            except:
                print(f"❌ Error abriendo {name}")

    def run(self):
        """Ejecuta la aplicación"""
        if GUI_AVAILABLE and hasattr(self, 'root'):
            self.add_log("🎉 VisiFruit Launcher Fixed listo", "success")
            self.root.mainloop()
        else:
            self.run_cli()

def main():
    """Punto de entrada principal"""
    try:
        print("🍎 VisiFruit Launcher Fixed v1.0")
        print("Compatible con Python 3.13 - Manejo mejorado de Tcl/Tk")
        
        app = VisiFruitLauncherFixed()
        app.run()
        
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        input("Presiona Enter para salir...")

if __name__ == "__main__":
    main()
