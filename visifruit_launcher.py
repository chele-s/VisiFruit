#!/usr/bin/env python3
"""
VisiFruit Launcher - Interfaz Gráfica Moderna
==============================================

Launcher visual y elegante para el sistema VisiFruit.
Incluye:
- Interfaz moderna con tema oscuro/claro
- Logs visuales con colores
- Monitoreo de estado en tiempo real
- Apertura automática del navegador
- Control completo del sistema

Autor: Asistente IA para VisiFruit
Versión: 1.0.0
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import requests

# Intentar importar customtkinter para interfaz moderna
try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
    ctk.set_appearance_mode("dark")  # Tema oscuro por defecto
    ctk.set_default_color_theme("blue")
except ImportError:
    CTK_AVAILABLE = False
    print("CustomTkinter no disponible. Usando tkinter estándar.")

class ModernButton:
    """Botón moderno que funciona con o sin customtkinter"""
    
    def __init__(self, parent, text="", command=None, color="blue", **kwargs):
        if CTK_AVAILABLE:
            self.button = ctk.CTkButton(
                parent, 
                text=text, 
                command=command,
                **kwargs
            )
        else:
            self.button = tk.Button(
                parent,
                text=text,
                command=command,
                bg="#1f538d" if color == "blue" else "#d32f2f" if color == "red" else "#388e3c",
                fg="white",
                font=("Arial", 10, "bold"),
                relief="flat",
                bd=0,
                padx=20,
                pady=10,
                **kwargs
            )
    
    def pack(self, **kwargs):
        self.button.pack(**kwargs)
    
    def grid(self, **kwargs):
        self.button.grid(**kwargs)
    
    def configure(self, **kwargs):
        self.button.configure(**kwargs)

class VisiFruitLauncher:
    """Launcher principal del sistema VisiFruit"""
    
    def __init__(self):
        # Configuración inicial
        self.root_path = Path.cwd()
        self.backend_process = None
        self.frontend_process = None
        self.system_process = None
        self.monitoring_thread = None
        self.is_monitoring = False
        
        # Estado del sistema
        self.system_status = {
            "backend": "stopped",
            "frontend": "stopped",
            "system": "stopped",
            "ports": {"8001": False, "3000": False, "8000": False}
        }
        
        # Configurar logging
        self.setup_logging()
        
        # Crear ventana principal
        self.create_main_window()
        
        # Configurar interfaz
        self.setup_interface()
        
        # Iniciar monitoreo
        self.start_monitoring()

    def setup_logging(self):
        """Configura el sistema de logging"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'launcher.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def create_main_window(self):
        """Crea la ventana principal"""
        if CTK_AVAILABLE:
            self.root = ctk.CTk()
            self.root.title("🍎 VisiFruit Launcher v1.0")
            self.root.geometry("1000x700")
            self.root.resizable(True, True)
        else:
            self.root = tk.Tk()
            self.root.title("🍎 VisiFruit Launcher v1.0")
            self.root.geometry("1000x700")
            self.root.configure(bg="#2b2b2b")
        
        # Configurar icono (si existe)
        try:
            if Path("Others/Images/VisiFruit Logo.png").exists():
                # En una implementación completa, aquí se configuraría el icono
                pass
        except:
            pass
        
        # Configurar cierre
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_interface(self):
        """Configura toda la interfaz"""
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
        
        # Panel de enlaces rápidos
        self.create_links_panel(main_frame)

    def create_header(self, parent):
        """Crea el header con título y logo"""
        if CTK_AVAILABLE:
            header_frame = ctk.CTkFrame(parent)
            header_frame.pack(fill="x", pady=(0, 20))
            
            title_label = ctk.CTkLabel(
                header_frame,
                text="🍎 VisiFruit System Launcher",
                font=ctk.CTkFont(size=28, weight="bold")
            )
            title_label.pack(pady=20)
            
            subtitle_label = ctk.CTkLabel(
                header_frame,
                text="Sistema Industrial de Etiquetado de Frutas v3.0",
                font=ctk.CTkFont(size=14)
            )
            subtitle_label.pack(pady=(0, 10))
        else:
            header_frame = tk.Frame(parent, bg="#2b2b2b")
            header_frame.pack(fill="x", pady=(0, 20))
            
            title_label = tk.Label(
                header_frame,
                text="🍎 VisiFruit System Launcher",
                font=("Arial", 24, "bold"),
                bg="#2b2b2b",
                fg="white"
            )
            title_label.pack(pady=20)
            
            subtitle_label = tk.Label(
                header_frame,
                text="Sistema Industrial de Etiquetado de Frutas v3.0",
                font=("Arial", 12),
                bg="#2b2b2b",
                fg="#cccccc"
            )
            subtitle_label.pack()

    def create_control_panel(self, parent):
        """Crea el panel de control principal"""
        if CTK_AVAILABLE:
            control_frame = ctk.CTkFrame(parent)
            control_frame.pack(fill="x", pady=(0, 20))
            
            title = ctk.CTkLabel(
                control_frame,
                text="🎮 Control del Sistema",
                font=ctk.CTkFont(size=18, weight="bold")
            )
            title.pack(pady=(15, 10))
        else:
            control_frame = tk.LabelFrame(
                parent,
                text="🎮 Control del Sistema",
                font=("Arial", 14, "bold"),
                bg="#2b2b2b",
                fg="white",
                bd=2,
                relief="groove"
            )
            control_frame.pack(fill="x", pady=(0, 20), padx=10)
        
        # Frame para botones
        if CTK_AVAILABLE:
            buttons_frame = ctk.CTkFrame(control_frame)
            buttons_frame.pack(pady=15, padx=15)
        else:
            buttons_frame = tk.Frame(control_frame, bg="#2b2b2b")
            buttons_frame.pack(pady=15)
        
        # Botones principales
        self.start_all_btn = ModernButton(
            buttons_frame,
            text="🚀 Iniciar Sistema Completo",
            command=self.start_complete_system,
            color="blue"
        )
        self.start_all_btn.pack(side="left", padx=10)
        
        self.stop_all_btn = ModernButton(
            buttons_frame,
            text="⏹️ Detener Todo",
            command=self.stop_all_services,
            color="red"
        )
        self.stop_all_btn.pack(side="left", padx=10)
        
        # Frame para botones individuales
        if CTK_AVAILABLE:
            individual_frame = ctk.CTkFrame(control_frame)
            individual_frame.pack(pady=(10, 15), padx=15)
        else:
            individual_frame = tk.Frame(control_frame, bg="#2b2b2b")
            individual_frame.pack(pady=(10, 15))
        
        self.backend_btn = ModernButton(
            individual_frame,
            text="🔧 Backend",
            command=self.toggle_backend
        )
        self.backend_btn.pack(side="left", padx=5)
        
        self.frontend_btn = ModernButton(
            individual_frame,
            text="💻 Frontend",
            command=self.toggle_frontend
        )
        self.frontend_btn.pack(side="left", padx=5)
        
        self.system_btn = ModernButton(
            individual_frame,
            text="🏭 Sistema Principal",
            command=self.toggle_main_system
        )
        self.system_btn.pack(side="left", padx=5)

    def create_status_panel(self, parent):
        """Crea el panel de estado"""
        if CTK_AVAILABLE:
            status_frame = ctk.CTkFrame(parent)
            status_frame.pack(fill="x", pady=(0, 20))
            
            title = ctk.CTkLabel(
                status_frame,
                text="📊 Estado del Sistema",
                font=ctk.CTkFont(size=18, weight="bold")
            )
            title.pack(pady=(15, 10))
        else:
            status_frame = tk.LabelFrame(
                parent,
                text="📊 Estado del Sistema",
                font=("Arial", 14, "bold"),
                bg="#2b2b2b",
                fg="white",
                bd=2,
                relief="groove"
            )
            status_frame.pack(fill="x", pady=(0, 20), padx=10)
        
        # Frame para indicadores
        if CTK_AVAILABLE:
            indicators_frame = ctk.CTkFrame(status_frame)
            indicators_frame.pack(pady=15, padx=15, fill="x")
        else:
            indicators_frame = tk.Frame(status_frame, bg="#2b2b2b")
            indicators_frame.pack(pady=15, fill="x")
        
        # Indicadores de estado
        self.status_labels = {}
        services = [
            ("Backend (Puerto 8001)", "backend"),
            ("Frontend (Puerto 3000)", "frontend"),
            ("Sistema Principal (Puerto 8000)", "system")
        ]
        
        for i, (name, key) in enumerate(services):
            if CTK_AVAILABLE:
                frame = ctk.CTkFrame(indicators_frame)
                frame.grid(row=0, column=i, padx=10, pady=5, sticky="ew")
                
                label = ctk.CTkLabel(frame, text=name)
                label.pack(pady=(10, 5))
                
                self.status_labels[key] = ctk.CTkLabel(
                    frame,
                    text="●",
                    font=ctk.CTkFont(size=20),
                    text_color="red"
                )
                self.status_labels[key].pack(pady=(0, 10))
            else:
                frame = tk.Frame(indicators_frame, bg="#3b3b3b", relief="raised", bd=1)
                frame.grid(row=0, column=i, padx=10, pady=5, sticky="ew")
                
                label = tk.Label(
                    frame,
                    text=name,
                    bg="#3b3b3b",
                    fg="white",
                    font=("Arial", 10)
                )
                label.pack(pady=(10, 5))
                
                self.status_labels[key] = tk.Label(
                    frame,
                    text="●",
                    bg="#3b3b3b",
                    fg="red",
                    font=("Arial", 20)
                )
                self.status_labels[key].pack(pady=(0, 10))
        
        # Configurar grid
        indicators_frame.grid_columnconfigure(0, weight=1)
        indicators_frame.grid_columnconfigure(1, weight=1)
        indicators_frame.grid_columnconfigure(2, weight=1)

    def create_logs_panel(self, parent):
        """Crea el panel de logs"""
        if CTK_AVAILABLE:
            logs_frame = ctk.CTkFrame(parent)
            logs_frame.pack(fill="both", expand=True, pady=(0, 20))
            
            title = ctk.CTkLabel(
                logs_frame,
                text="📝 Registro de Actividad",
                font=ctk.CTkFont(size=18, weight="bold")
            )
            title.pack(pady=(15, 10))
        else:
            logs_frame = tk.LabelFrame(
                parent,
                text="📝 Registro de Actividad",
                font=("Arial", 14, "bold"),
                bg="#2b2b2b",
                fg="white",
                bd=2,
                relief="groove"
            )
            logs_frame.pack(fill="both", expand=True, pady=(0, 20), padx=10)
        
        # Text widget para logs
        if CTK_AVAILABLE:
            self.logs_text = ctk.CTkTextbox(
                logs_frame,
                height=200,
                font=ctk.CTkFont(family="Consolas", size=11)
            )
            self.logs_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        else:
            self.logs_text = scrolledtext.ScrolledText(
                logs_frame,
                height=12,
                bg="#1e1e1e",
                fg="#ffffff",
                font=("Consolas", 10),
                insertbackground="white"
            )
            self.logs_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Agregar log inicial
        self.add_log("🚀 VisiFruit Launcher iniciado", "info")

    def create_links_panel(self, parent):
        """Crea el panel de enlaces rápidos"""
        if CTK_AVAILABLE:
            links_frame = ctk.CTkFrame(parent)
            links_frame.pack(fill="x")
            
            title = ctk.CTkLabel(
                links_frame,
                text="🔗 Enlaces Rápidos",
                font=ctk.CTkFont(size=18, weight="bold")
            )
            title.pack(pady=(15, 10))
        else:
            links_frame = tk.LabelFrame(
                parent,
                text="🔗 Enlaces Rápidos",
                font=("Arial", 14, "bold"),
                bg="#2b2b2b",
                fg="white",
                bd=2,
                relief="groove"
            )
            links_frame.pack(fill="x", padx=10)
        
        # Frame para botones de enlace
        if CTK_AVAILABLE:
            buttons_frame = ctk.CTkFrame(links_frame)
            buttons_frame.pack(pady=15, padx=15)
        else:
            buttons_frame = tk.Frame(links_frame, bg="#2b2b2b")
            buttons_frame.pack(pady=15)
        
        # Botones de enlace
        links = [
            ("🌐 Frontend (3000)", "http://localhost:3000"),
            ("🔧 Backend API (8001)", "http://localhost:8001/api/docs"),
            ("🏭 Sistema Principal (8000)", "http://localhost:8000"),
            ("📊 WebSocket Test", "ws://localhost:8001/ws")
        ]
        
        for text, url in links:
            btn = ModernButton(
                buttons_frame,
                text=text,
                command=lambda u=url: self.open_url(u)
            )
            btn.pack(side="left", padx=5)

    def add_log(self, message: str, level: str = "info"):
        """Añade un mensaje al log con formato"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Emojis por nivel
        emojis = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "debug": "🔍"
        }
        
        emoji = emojis.get(level, "📝")
        formatted_message = f"[{timestamp}] {emoji} {message}\n"
        
        # Configurar colores si es tkinter estándar
        if not CTK_AVAILABLE:
            colors = {
                "info": "#ffffff",
                "success": "#4caf50",
                "warning": "#ff9800",
                "error": "#f44336",
                "debug": "#2196f3"
            }
            
            # Configurar tags de color
            color = colors.get(level, "#ffffff")
            tag_name = f"color_{level}"
            self.logs_text.tag_configure(tag_name, foreground=color)
        
        # Añadir al widget
        if CTK_AVAILABLE:
            self.logs_text.insert("end", formatted_message)
        else:
            self.logs_text.insert(tk.END, formatted_message, f"color_{level}")
        
        # Auto-scroll
        if CTK_AVAILABLE:
            pass  # CTkTextbox hace auto-scroll automáticamente
        else:
            self.logs_text.see(tk.END)
        
        # Actualizar GUI
        self.root.update_idletasks()

    def check_ports(self) -> Dict[str, bool]:
        """Verifica qué puertos están en uso"""
        ports_status = {}
        ports_to_check = [8000, 8001, 3000]
        
        for port in ports_to_check:
            try:
                response = requests.get(f"http://localhost:{port}/health", timeout=2)
                ports_status[str(port)] = response.status_code == 200
            except:
                ports_status[str(port)] = False
        
        return ports_status

    def update_status_indicators(self):
        """Actualiza los indicadores de estado"""
        # Verificar puertos
        self.system_status["ports"] = self.check_ports()
        
        # Actualizar indicadores visuales
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
        """Inicia el monitoreo en hilo separado"""
        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
        self.monitoring_thread.start()

    def monitoring_loop(self):
        """Bucle de monitoreo"""
        while self.is_monitoring:
            try:
                self.update_status_indicators()
                time.sleep(3)  # Verificar cada 3 segundos
            except Exception as e:
                self.logger.error(f"Error en monitoreo: {e}")
                time.sleep(5)

    def start_complete_system(self):
        """Inicia el sistema completo"""
        self.add_log("🚀 Iniciando sistema completo...", "info")
        
        try:
            # Verificar que estamos en la ubicación correcta
            if not Path("main_etiquetadora.py").exists():
                self.add_log("❌ Error: No se encuentra main_etiquetadora.py", "error")
                messagebox.showerror("Error", "No estás en la raíz del proyecto VisiFruit")
                return
            
            # Ejecutar script de inicio completo
            if sys.platform == "win32":
                script_path = "start_sistema_completo.ps1"
                if Path(script_path).exists():
                    self.add_log("🔧 Ejecutando script PowerShell...", "info")
                    subprocess.Popen([
                        "powershell", "-ExecutionPolicy", "Bypass", "-File", script_path
                    ], creationflags=subprocess.CREATE_NEW_CONSOLE)
                else:
                    # Fallback a .bat
                    script_path = "start_sistema_completo.bat"
                    subprocess.Popen([script_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
            
            self.add_log("✅ Sistema completo iniciado", "success")
            
            # Esperar un poco y abrir navegador
            threading.Timer(8.0, self.open_frontend_browser).start()
            
        except Exception as e:
            self.add_log(f"❌ Error iniciando sistema: {e}", "error")
            self.logger.error(f"Error iniciando sistema completo: {e}")

    def open_frontend_browser(self):
        """Abre el navegador con el frontend"""
        try:
            webbrowser.open("http://localhost:3000")
            self.add_log("🌐 Frontend abierto en navegador", "success")
        except Exception as e:
            self.add_log(f"⚠️ No se pudo abrir navegador: {e}", "warning")

    def stop_all_services(self):
        """Detiene todos los servicios"""
        self.add_log("⏹️ Deteniendo todos los servicios...", "warning")
        
        try:
            # Intentar detener procesos conocidos
            if sys.platform == "win32":
                # Matar procesos por puerto
                ports = [8000, 8001, 3000]
                for port in ports:
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

    def toggle_backend(self):
        """Inicia/detiene solo el backend"""
        if self.system_status["backend"] == "running":
            self.add_log("⏹️ Deteniendo backend...", "warning")
            # Lógica para detener backend
        else:
            self.add_log("🔧 Iniciando backend...", "info")
            try:
                script_path = "start_backend.bat"
                if Path(script_path).exists():
                    subprocess.Popen([script_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
                    self.add_log("✅ Backend iniciado", "success")
            except Exception as e:
                self.add_log(f"❌ Error iniciando backend: {e}", "error")

    def toggle_frontend(self):
        """Inicia/detiene solo el frontend"""
        if self.system_status["frontend"] == "running":
            self.add_log("⏹️ Deteniendo frontend...", "warning")
            # Lógica para detener frontend
        else:
            self.add_log("💻 Iniciando frontend...", "info")
            try:
                script_path = "start_frontend.bat"
                if Path(script_path).exists():
                    subprocess.Popen([script_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
                    self.add_log("✅ Frontend iniciado", "success")
                    # Abrir navegador después de 5 segundos
                    threading.Timer(5.0, self.open_frontend_browser).start()
            except Exception as e:
                self.add_log(f"❌ Error iniciando frontend: {e}", "error")

    def toggle_main_system(self):
        """Inicia/detiene el sistema principal de etiquetado"""
        if self.system_status["system"] == "running":
            self.add_log("⏹️ Deteniendo sistema principal...", "warning")
            # Lógica para detener sistema principal
        else:
            self.add_log("🏭 Iniciando sistema principal de etiquetado...", "info")
            try:
                # Ejecutar el sistema principal
                subprocess.Popen([
                    sys.executable, "main_etiquetadora.py"
                ], creationflags=subprocess.CREATE_NEW_CONSOLE)
                self.add_log("✅ Sistema principal iniciado", "success")
            except Exception as e:
                self.add_log(f"❌ Error iniciando sistema principal: {e}", "error")

    def open_url(self, url: str):
        """Abre una URL en el navegador"""
        try:
            if url.startswith("ws://"):
                # Para WebSockets, abrir herramienta de test
                test_url = "https://www.websocket.org/echo.html"
                webbrowser.open(test_url)
                self.add_log(f"🔗 Herramienta WebSocket abierta", "info")
            else:
                webbrowser.open(url)
                self.add_log(f"🌐 Abierto: {url}", "info")
        except Exception as e:
            self.add_log(f"❌ Error abriendo URL: {e}", "error")

    def on_closing(self):
        """Maneja el cierre de la aplicación"""
        if messagebox.askokcancel("Salir", "¿Estás seguro de que quieres cerrar el launcher?"):
            self.is_monitoring = False
            self.add_log("👋 Cerrando VisiFruit Launcher...", "info")
            self.root.destroy()

    def run(self):
        """Ejecuta la aplicación"""
        self.add_log("🎉 VisiFruit Launcher listo", "success")
        self.root.mainloop()


def main():
    """Punto de entrada principal"""
    try:
        app = VisiFruitLauncher()
        app.run()
    except Exception as e:
        print(f"Error fatal: {e}")
        input("Presiona Enter para salir...")


if __name__ == "__main__":
    main()
