# service_manager.py
"""
Gestor de Servicios Auxiliares FruPrint v4.0
============================================

Sistema de auto-inicio y gestión de servicios auxiliares
(frontend React, backend dashboard, limpieza preventiva).

Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Septiembre 2025
Versión: 4.0 - MODULAR ARCHITECTURE
"""

import os
import sys
import time
import signal
import asyncio
import logging
import subprocess
import shutil
import atexit
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# ==================== VARIABLES GLOBALES ====================

GLOBAL_SERVICES = {}
LOCK_FILE_PATH = Path("/tmp/visifruit_main.lock")

# ==================== GESTIÓN DE INSTANCIA ÚNICA ====================

def ensure_single_instance():
    """Evita múltiples instancias simultáneas del proceso principal."""
    try:
        if LOCK_FILE_PATH.exists():
            try:
                previous_pid = int(LOCK_FILE_PATH.read_text().strip() or "0")
            except Exception:
                previous_pid = 0

            if previous_pid and previous_pid != os.getpid():
                is_same_app = False
                try:
                    cmdline_path = f"/proc/{previous_pid}/cmdline"
                    with open(cmdline_path, "rb") as f:
                        cmdline = f.read().decode(errors="ignore")
                        if "main_etiquetadora.py" in cmdline:
                            is_same_app = True
                except Exception:
                    pass

                try:
                    os.kill(previous_pid, 0)
                    process_exists = True
                except ProcessLookupError:
                    process_exists = False

                if process_exists and is_same_app and os.getenv("ALLOW_MULTIPLE_INSTANCES", "false").lower() != "true":
                    print(f"⚠️ Otra instancia ya está en ejecución (PID {previous_pid}).")
                    print("   Para permitir múltiples instancias: export ALLOW_MULTIPLE_INSTANCES=true")
                    sys.exit(1)
                elif not process_exists or not is_same_app:
                    try:
                        LOCK_FILE_PATH.unlink(missing_ok=True)
                    except Exception:
                        pass

        try:
            LOCK_FILE_PATH.write_text(str(os.getpid()))
        except Exception:
            pass
            
    except Exception:
        pass

def _sync_force_kill_services():
    """Cierre de seguridad sincronizado para servicios auxiliares."""
    try:
        for name, process in list(GLOBAL_SERVICES.items()):
            try:
                if process and process.returncode is None:
                    try:
                        os.killpg(process.pid, signal.SIGTERM)
                    except Exception:
                        try:
                            process.terminate()
                        except Exception:
                            pass
                    time.sleep(0.5)
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except Exception:
                        try:
                            process.kill()
                        except Exception:
                            pass
            except Exception:
                pass
    except Exception:
        pass

@atexit.register
def _on_exit_cleanup():
    """Limpieza al salir del proceso."""
    try:
        _sync_force_kill_services()
    finally:
        try:
            LOCK_FILE_PATH.unlink(missing_ok=True)
        except Exception:
            pass

# ==================== LIMPIEZA PREVENTIVA ====================

def preflight_cleanup():
    """Limpieza preventiva de conflictos comunes."""
    # Matar instancias previas
    try:
        current_pid = os.getpid()
        try:
            output = subprocess.check_output(["pgrep", "-f", "main_etiquetadora.py"], text=True)
        except subprocess.CalledProcessError:
            output = ""
        
        pids = []
        for line in output.strip().splitlines():
            try:
                pid = int(line.strip())
                if pid != current_pid:
                    pids.append(pid)
            except Exception:
                continue
        
        for pid in pids:
            try:
                os.kill(pid, signal.SIGTERM)
            except Exception:
                pass
        
        time.sleep(0.3)
        
        for pid in pids:
            try:
                os.kill(pid, signal.SIGKILL)
            except Exception:
                pass
    except Exception:
        pass

    # Liberar puertos
    for port in ("8002", "8001", "3000", "8000"):
        try:
            if shutil.which("fuser"):
                subprocess.run(
                    ["fuser", "-k", f"{port}/tcp"], 
                    check=False, 
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.DEVNULL
                )
        except Exception:
            pass

    # Detener servicios de cámara de escritorio
    if os.getenv("DISABLE_DESKTOP_CAMERA_SERVICES", "true").lower() == "true":
        try:
            subprocess.run([
                "systemctl", "--user", "stop", "--now",
                "pipewire.service", "pipewire.socket", "wireplumber.service"
            ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

# ==================== CARGA DE VARIABLES DE ENTORNO ====================

def load_env_variables():
    """Carga variables de entorno desde archivo .env si existe."""
    env_file = Path(".env")
    if env_file.exists():
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
            logger.info("✅ Variables de entorno cargadas desde .env")
        except Exception as e:
            logger.warning(f"⚠️ Error cargando .env: {e}")
    else:
        logger.info("ℹ️ Archivo .env no encontrado - usando variables del sistema")

# ==================== AUTO-INICIO DE SERVICIOS ====================

async def start_frontend_process():
    """Inicia el proceso del frontend React."""
    try:
        frontend_dir = Path("Interfaz_Usuario/VisiFruit")
        if not frontend_dir.exists():
            logger.warning("❌ Directorio del frontend no encontrado")
            return None
        
        if not shutil.which("npm"):
            logger.warning("❌ npm no encontrado - frontend no se puede iniciar")
            return None
        
        node_modules = frontend_dir / "node_modules"
        if not node_modules.exists():
            logger.info("📦 Instalando dependencias del frontend...")
            install_process = await asyncio.create_subprocess_exec(
                "npm", "install",
                cwd=str(frontend_dir),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE
            )
            await install_process.wait()
            if install_process.returncode != 0:
                logger.error("❌ Error instalando dependencias del frontend")
                return None
        
        env = os.environ.copy()
        env.update({
            "VITE_API_URL": os.getenv("VITE_API_URL", "http://localhost:8001"),
            "VITE_WS_URL": os.getenv("VITE_WS_URL", "ws://localhost:8001/ws/realtime"),
            "VITE_MAIN_API_URL": os.getenv("VITE_MAIN_API_URL", "http://localhost:8000"),
            "NODE_ENV": os.getenv("NODE_ENV", "development")
        })
        
        logger.info("🚀 Iniciando servidor frontend en puerto 3000...")
        frontend_process = await asyncio.create_subprocess_exec(
            "npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000",
            cwd=str(frontend_dir),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            start_new_session=True
        )
        
        logger.info("✅ Frontend iniciado en http://0.0.0.0:3000")
        return frontend_process
        
    except Exception as e:
        logger.error(f"❌ Error iniciando frontend: {e}")
        return None

async def start_backend_process():
    """Inicia el proceso del backend dashboard."""
    try:
        backend_dir = Path("Interfaz_Usuario/Backend")
        if not backend_dir.exists():
            logger.warning("❌ Directorio del backend no encontrado")
            return None
        
        python_executable = sys.executable
        
        logger.info("🚀 Iniciando servidor backend dashboard en puerto 8001...")
        backend_process = await asyncio.create_subprocess_exec(
            python_executable, "-u", "main.py",
            cwd=str(backend_dir),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            start_new_session=True
        )
        
        logger.info("✅ Backend dashboard iniciado en http://0.0.0.0:8001")
        return backend_process
        
    except Exception as e:
        logger.error(f"❌ Error iniciando backend dashboard: {e}")
        return None

async def check_and_start_services(start_frontend: bool = True, start_backend: bool = True):
    """Verifica y inicia los servicios frontend y backend si está habilitado."""
    services = {}
    
    load_env_variables()
    
    auto_start_frontend = os.getenv("AUTO_START_FRONTEND", "true").lower() == "true" and start_frontend
    auto_start_backend = os.getenv("AUTO_START_BACKEND", "true").lower() == "true" and start_backend
    
    if auto_start_backend:
        logger.info("🔄 Iniciando backend dashboard automáticamente...")
        backend_process = await start_backend_process()
        if backend_process:
            services["backend"] = backend_process
            await asyncio.sleep(3)
    
    if auto_start_frontend:
        logger.info("🔄 Iniciando frontend automáticamente...")
        frontend_process = await start_frontend_process()
        if frontend_process:
            services["frontend"] = frontend_process
            await asyncio.sleep(5)
    
    if services:
        GLOBAL_SERVICES.clear()
        GLOBAL_SERVICES.update(services)
        logger.info(f"✅ Servicios iniciados: {list(services.keys())}")
        logger.info("🌐 URLs disponibles:")
        if "backend" in services:
            logger.info("   📊 Dashboard Backend: http://localhost:8001")
            logger.info("   📄 Documentación API: http://localhost:8001/docs")
        if "frontend" in services:
            logger.info("   🎨 Interfaz Frontend: http://localhost:3000")
        logger.info("   🏷️ Sistema Principal: http://localhost:8000")
    
    return services

async def cleanup_services(services: Dict):
    """Limpia los procesos de servicios al cerrar."""
    for service_name, process in services.items():
        try:
            if process and process.returncode is None:
                logger.info(f"🛑 Deteniendo {service_name}...")
                try:
                    process.terminate()
                except Exception:
                    pass
                
                try:
                    await asyncio.wait_for(process.wait(), timeout=10)
                except asyncio.TimeoutError:
                    logger.warning(f"⚠️ Forzando cierre de {service_name}")
                    try:
                        os.killpg(process.pid, signal.SIGTERM)
                    except Exception:
                        try:
                            process.kill()
                        except Exception:
                            pass
                    
                    try:
                        await asyncio.wait_for(process.wait(), timeout=5)
                    except Exception:
                        try:
                            os.killpg(process.pid, signal.SIGKILL)
                        except Exception:
                            pass
                
                logger.info(f"✅ {service_name} detenido")
        except Exception as e:
            logger.error(f"❌ Error deteniendo {service_name}: {e}")

__all__ = [
    'ensure_single_instance', 'preflight_cleanup', 'load_env_variables',
    'check_and_start_services', 'cleanup_services', 'GLOBAL_SERVICES'
]
