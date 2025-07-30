#!/usr/bin/env python3
# install_fruprint.py
"""
Script de Instalación Automatizada - FruPrint Industrial v2.0
============================================================

Script inteligente para instalación y configuración del sistema FruPrint
en diferentes plataformas con detección automática de hardware.

Características:
- Detección automática de plataforma (Raspberry Pi, Linux, Windows, macOS)
- Instalación de dependencias del sistema
- Configuración de entorno virtual
- Instalación de dependencias Python optimizada
- Configuración inicial del sistema
- Validación de instalación completa
- Configuración de servicios del sistema

Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Diciembre 2024
Versión: 2.0 - Edición Industrial
"""

import os
import sys
import subprocess
import platform
import logging
import json
import shutil
import venv
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('fruprint_install.log')
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class SystemInfo:
    """Información del sistema detectada."""
    platform: str
    is_raspberry_pi: bool
    python_version: str
    architecture: str
    total_memory_gb: float
    cpu_cores: int
    has_gpio: bool
    has_camera: bool

class FruPrintInstaller:
    """Instalador inteligente del sistema FruPrint."""
    
    def __init__(self):
        self.system_info = self._detect_system()
        self.project_root = Path.cwd()
        self.venv_path = self.project_root / "venv"
        self.config_path = self.project_root / "Config_Etiquetadora.json"
        
        logger.info("=== Instalador FruPrint Industrial v2.0 ===")
        logger.info(f"Plataforma detectada: {self.system_info.platform}")
        logger.info(f"Python: {self.system_info.python_version}")
        logger.info(f"Arquitectura: {self.system_info.architecture}")
        logger.info(f"Memoria: {self.system_info.total_memory_gb:.1f}GB")
        logger.info(f"CPU cores: {self.system_info.cpu_cores}")
        
        if self.system_info.is_raspberry_pi:
            logger.info("🍓 Raspberry Pi detectado - Configuración industrial")
        
    def _detect_system(self) -> SystemInfo:
        """Detecta información del sistema."""
        import psutil
        
        platform_name = platform.system().lower()
        machine = platform.machine().lower()
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        
        # Detectar Raspberry Pi
        is_raspberry_pi = False
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read().lower()
                is_raspberry_pi = 'raspberry pi' in cpuinfo or 'bcm' in cpuinfo
        except:
            pass
        
        # Detectar GPIO
        has_gpio = is_raspberry_pi or os.path.exists('/dev/gpiomem')
        
        # Detectar cámara
        has_camera = (
            os.path.exists('/dev/video0') or 
            os.path.exists('/opt/vc/bin/vcgencmd') or
            len([p for p in Path('/dev').glob('video*')]) > 0
        )
        
        return SystemInfo(
            platform=platform_name,
            is_raspberry_pi=is_raspberry_pi,
            python_version=python_version,
            architecture=machine,
            total_memory_gb=psutil.virtual_memory().total / (1024**3),
            cpu_cores=psutil.cpu_count(),
            has_gpio=has_gpio,
            has_camera=has_camera
        )
    
    def install(self) -> bool:
        """Ejecuta la instalación completa."""
        try:
            logger.info("Iniciando instalación de FruPrint Industrial...")
            
            # Verificaciones previas
            if not self._check_prerequisites():
                return False
            
            # Instalar dependencias del sistema
            if not self._install_system_dependencies():
                logger.error("Fallo al instalar dependencias del sistema")
                return False
            
            # Crear entorno virtual
            if not self._create_virtual_environment():
                logger.error("Fallo al crear entorno virtual")
                return False
            
            # Instalar dependencias Python
            if not self._install_python_dependencies():
                logger.error("Fallo al instalar dependencias Python")
                return False
            
            # Configurar sistema
            if not self._configure_system():
                logger.error("Fallo al configurar sistema")
                return False
            
            # Validar instalación
            if not self._validate_installation():
                logger.error("Fallo en validación de instalación")
                return False
            
            # Configurar servicios (opcional)
            self._setup_services()
            
            logger.info("✅ Instalación completada exitosamente!")
            self._print_next_steps()
            
            return True
            
        except Exception as e:
            logger.exception(f"Error durante instalación: {e}")
            return False
    
    def _check_prerequisites(self) -> bool:
        """Verifica prerrequisitos del sistema."""
        logger.info("Verificando prerrequisitos...")
        
        # Verificar Python version
        if sys.version_info < (3, 8):
            logger.error(f"Python 3.8+ requerido, encontrado {self.system_info.python_version}")
            return False
        
        # Verificar memoria
        if self.system_info.total_memory_gb < 2:
            logger.warning(f"Memoria baja detectada: {self.system_info.total_memory_gb:.1f}GB")
            logger.warning("Se recomienda al menos 2GB para operación óptima")
        
        # Verificar espacio en disco
        disk_usage = shutil.disk_usage(self.project_root)
        free_gb = disk_usage.free / (1024**3)
        
        if free_gb < 5:
            logger.error(f"Espacio insuficiente en disco: {free_gb:.1f}GB libres")
            logger.error("Se requieren al menos 5GB libres")
            return False
        
        logger.info("✅ Prerrequisitos verificados")
        return True
    
    def _install_system_dependencies(self) -> bool:
        """Instala dependencias del sistema operativo."""
        logger.info("Instalando dependencias del sistema...")
        
        if self.system_info.platform == "linux":
            return self._install_linux_dependencies()
        elif self.system_info.platform == "darwin":
            return self._install_macos_dependencies()
        elif self.system_info.platform == "windows":
            return self._install_windows_dependencies()
        else:
            logger.warning(f"Plataforma no soportada completamente: {self.system_info.platform}")
            return True
    
    def _install_linux_dependencies(self) -> bool:
        """Instala dependencias en Linux/Raspberry Pi."""
        packages = [
            # Desarrollo
            "python3-dev", "python3-pip", "python3-venv",
            "build-essential", "cmake", "pkg-config",
            
            # OpenCV y visión
            "libopencv-dev", "python3-opencv",
            "libgl1-mesa-glx", "libglib2.0-0",
            "libjpeg-dev", "libpng-dev", "libtiff-dev",
            "libv4l-dev", "v4l-utils",
            
            # Matemáticas y ciencia
            "libatlas-base-dev", "libhdf5-dev", "libhdf5-serial-dev",
            "libblas-dev", "liblapack-dev", "gfortran",
            
            # Sistema
            "git", "curl", "wget", "nano",
            "htop", "tree", "unzip",
        ]
        
        if self.system_info.is_raspberry_pi:
            packages.extend([
                # GPIO para Raspberry Pi
                "python3-rpi.gpio", "pigpio", "python3-pigpio",
                
                # Cámara Raspberry Pi
                "libraspberrypi-bin", "libraspberrypi-dev",
                
                # I2C/SPI
                "python3-smbus", "i2c-tools", "python3-spidev",
            ])
        
        try:
            # Actualizar repositorios
            logger.info("Actualizando repositorios...")
            subprocess.run(["sudo", "apt-get", "update"], check=True, capture_output=True)
            
            # Instalar paquetes
            logger.info("Instalando paquetes del sistema...")
            cmd = ["sudo", "apt-get", "install", "-y"] + packages
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Error instalando paquetes: {result.stderr}")
                return False
            
            # Configuraciones específicas de Raspberry Pi
            if self.system_info.is_raspberry_pi:
                self._configure_raspberry_pi()
            
            logger.info("✅ Dependencias del sistema instaladas")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error ejecutando comando del sistema: {e}")
            return False
        except Exception as e:
            logger.error(f"Error instalando dependencias: {e}")
            return False
    
    def _configure_raspberry_pi(self):
        """Configuraciones específicas para Raspberry Pi."""
        logger.info("Configurando Raspberry Pi...")
        
        try:
            # Habilitar cámara e I2C
            logger.info("Habilitando cámara e I2C...")
            
            # Verificar si raspi-config está disponible
            if shutil.which("raspi-config"):
                # Habilitar cámara
                subprocess.run([
                    "sudo", "raspi-config", "nonint", "do_camera", "0"
                ], capture_output=True)
                
                # Habilitar I2C
                subprocess.run([
                    "sudo", "raspi-config", "nonint", "do_i2c", "0"
                ], capture_output=True)
                
                # Habilitar SPI
                subprocess.run([
                    "sudo", "raspi-config", "nonint", "do_spi", "0"
                ], capture_output=True)
            
            # Aumentar memoria GPU si es necesario
            config_txt = Path("/boot/config.txt")
            if config_txt.exists():
                with open(config_txt, "r") as f:
                    content = f.read()
                
                if "gpu_mem" not in content:
                    logger.info("Configurando memoria GPU...")
                    with open("gpu_mem_config.txt", "w") as f:
                        f.write("\\n# FruPrint - Configuración GPU\\ngpu_mem=128\\n")
                    
                    subprocess.run([
                        "sudo", "sh", "-c", 
                        "cat gpu_mem_config.txt >> /boot/config.txt"
                    ], capture_output=True)
                    
                    os.remove("gpu_mem_config.txt")
            
            logger.info("✅ Raspberry Pi configurado")
            
        except Exception as e:
            logger.warning(f"Error configurando Raspberry Pi: {e}")
    
    def _install_macos_dependencies(self) -> bool:
        """Instala dependencias en macOS."""
        logger.info("Instalando dependencias para macOS...")
        
        # Verificar Homebrew
        if not shutil.which("brew"):
            logger.error("Homebrew no encontrado. Instale Homebrew primero:")
            logger.error("/bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
            return False
        
        packages = [
            "python@3.11", "opencv", "cmake", "pkg-config",
            "jpeg", "libpng", "libtiff", "openexr", "libraw",
            "hdf5", "openblas", "lapack"
        ]
        
        try:
            for package in packages:
                logger.info(f"Instalando {package}...")
                result = subprocess.run(
                    ["brew", "install", package], 
                    capture_output=True, text=True
                )
                
                if result.returncode != 0 and "already installed" not in result.stderr:
                    logger.warning(f"Advertencia instalando {package}: {result.stderr}")
            
            logger.info("✅ Dependencias de macOS instaladas")
            return True
            
        except Exception as e:
            logger.error(f"Error instalando dependencias de macOS: {e}")
            return False
    
    def _install_windows_dependencies(self) -> bool:
        """Instala dependencias en Windows."""
        logger.info("Configurando para Windows...")
        
        # En Windows, la mayoría de dependencias se instalan vía pip
        logger.info("✅ Windows configurado (dependencias vía pip)")
        return True
    
    def _create_virtual_environment(self) -> bool:
        """Crea entorno virtual Python."""
        logger.info("Creando entorno virtual...")
        
        try:
            if self.venv_path.exists():
                logger.info("Entorno virtual existente encontrado, eliminando...")
                shutil.rmtree(self.venv_path)
            
            # Crear entorno virtual
            venv.create(self.venv_path, with_pip=True)
            
            # Verificar creación
            if self.system_info.platform == "windows":
                python_path = self.venv_path / "Scripts" / "python.exe"
                pip_path = self.venv_path / "Scripts" / "pip.exe"
            else:
                python_path = self.venv_path / "bin" / "python"
                pip_path = self.venv_path / "bin" / "pip"
            
            if not python_path.exists():
                logger.error("Fallo al crear entorno virtual")
                return False
            
            # Actualizar pip
            logger.info("Actualizando pip...")
            subprocess.run([
                str(python_path), "-m", "pip", "install", "--upgrade", "pip"
            ], check=True, capture_output=True)
            
            logger.info("✅ Entorno virtual creado")
            return True
            
        except Exception as e:
            logger.error(f"Error creando entorno virtual: {e}")
            return False
    
    def _install_python_dependencies(self) -> bool:
        """Instala dependencias Python."""
        logger.info("Instalando dependencias Python...")
        
        try:
            # Obtener rutas del entorno virtual
            if self.system_info.platform == "windows":
                python_path = self.venv_path / "Scripts" / "python.exe"
                pip_path = self.venv_path / "Scripts" / "pip.exe"
            else:
                python_path = self.venv_path / "bin" / "python"
                pip_path = self.venv_path / "bin" / "pip"
            
            # Instalar wheel primero
            subprocess.run([
                str(pip_path), "install", "wheel", "setuptools"
            ], check=True, capture_output=True)
            
            # Instalación optimizada para Raspberry Pi
            if self.system_info.is_raspberry_pi:
                return self._install_pi_dependencies(python_path, pip_path)
            else:
                return self._install_standard_dependencies(python_path, pip_path)
                
        except Exception as e:
            logger.error(f"Error instalando dependencias Python: {e}")
            return False
    
    def _install_pi_dependencies(self, python_path: Path, pip_path: Path) -> bool:
        """Instalación optimizada para Raspberry Pi."""
        logger.info("Instalación optimizada para Raspberry Pi...")
        
        # Dependencias críticas primero
        critical_packages = [
            "numpy>=1.24.0",
            "opencv-python>=4.8.0",
            "pillow>=10.0.0",
            "fastapi>=0.104.0",
            "uvicorn[standard]>=0.24.0",
            "pydantic>=2.5.0",
            "psutil>=5.9.0"
        ]
        
        # Instalar PyTorch para ARM
        torch_packages = [
            "torch>=2.0.0",
            "torchvision>=0.15.0"
        ]
        
        try:
            # Instalar críticas
            logger.info("Instalando dependencias críticas...")
            for package in critical_packages:
                logger.info(f"Instalando {package}...")
                result = subprocess.run([
                    str(pip_path), "install", "--prefer-binary", package
                ], capture_output=True, text=True, timeout=600)
                
                if result.returncode != 0:
                    logger.warning(f"Advertencia con {package}: {result.stderr}")
            
            # Instalar PyTorch
            logger.info("Instalando PyTorch...")
            result = subprocess.run([
                str(pip_path), "install", "--prefer-binary"
            ] + torch_packages, capture_output=True, text=True, timeout=1200)
            
            if result.returncode != 0:
                logger.warning(f"Advertencia con PyTorch: {result.stderr}")
            
            # Instalar resto de requirements
            requirements_file = self.project_root / "Requirements.txt"
            if requirements_file.exists():
                logger.info("Instalando resto de dependencias...")
                subprocess.run([
                    str(pip_path), "install", "-r", str(requirements_file)
                ], capture_output=True, timeout=1800)
            
            logger.info("✅ Dependencias de Raspberry Pi instaladas")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("Timeout durante instalación - proceso muy lento")
            return False
        except Exception as e:
            logger.error(f"Error en instalación Pi: {e}")
            return False
    
    def _install_standard_dependencies(self, python_path: Path, pip_path: Path) -> bool:
        """Instalación estándar para otras plataformas."""
        logger.info("Instalación estándar de dependencias...")
        
        try:
            requirements_file = self.project_root / "Requirements.txt"
            
            if not requirements_file.exists():
                logger.error("Archivo Requirements.txt no encontrado")
                return False
            
            # Instalar todas las dependencias
            logger.info("Instalando dependencias desde Requirements.txt...")
            result = subprocess.run([
                str(pip_path), "install", "-r", str(requirements_file)
            ], capture_output=True, text=True, timeout=1200)
            
            if result.returncode != 0:
                logger.error(f"Error instalando dependencias: {result.stderr}")
                return False
            
            logger.info("✅ Dependencias estándar instaladas")
            return True
            
        except Exception as e:
            logger.error(f"Error en instalación estándar: {e}")
            return False
    
    def _configure_system(self) -> bool:
        """Configura el sistema inicial."""
        logger.info("Configurando sistema...")
        
        try:
            # Crear directorios necesarios
            directories = [
                "logs", "data", "backups", "IA_Etiquetado/Models",
                "calibration", "temp"
            ]
            
            for directory in directories:
                dir_path = self.project_root / directory
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Directorio creado: {directory}")
            
            # Configurar archivo de configuración si no existe
            if not self.config_path.exists():
                logger.info("Creando configuración inicial...")
                self._create_initial_config()
            
            # Configurar permisos en Linux
            if self.system_info.platform == "linux":
                self._configure_linux_permissions()
            
            logger.info("✅ Sistema configurado")
            return True
            
        except Exception as e:
            logger.error(f"Error configurando sistema: {e}")
            return False
    
    def _create_initial_config(self):
        """Crea configuración inicial optimizada."""
        from utils.config_validator import ConfigValidator, ConfigProfile
        
        try:
            validator = ConfigValidator()
            
            # Seleccionar perfil según el sistema
            if self.system_info.is_raspberry_pi:
                if self.system_info.total_memory_gb >= 4:
                    profile = ConfigProfile.HIGH_PERFORMANCE
                else:
                    profile = ConfigProfile.ENERGY_EFFICIENT
            else:
                profile = ConfigProfile.DEVELOPMENT
            
            # Crear configuración
            config = validator.create_config_from_profile(profile)
            
            # Optimizar para hardware específico
            hardware_info = {
                'cpu_cores': self.system_info.cpu_cores,
                'ram_gb': self.system_info.total_memory_gb,
                'has_gpio': self.system_info.has_gpio,
                'has_camera': self.system_info.has_camera
            }
            
            config = validator.optimize_config_for_hardware(config, hardware_info)
            
            # Guardar configuración
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"Configuración inicial creada con perfil: {profile.value}")
            
        except Exception as e:
            logger.error(f"Error creando configuración inicial: {e}")
    
    def _configure_linux_permissions(self):
        """Configura permisos en Linux."""
        logger.info("Configurando permisos Linux...")
        
        try:
            # Agregar usuario a grupos necesarios
            import getpass
            username = getpass.getuser()
            
            groups = ["gpio", "i2c", "spi", "video", "dialout"]
            
            for group in groups:
                try:
                    subprocess.run([
                        "sudo", "usermod", "-a", "-G", group, username
                    ], capture_output=True, check=False)
                except:
                    pass
            
            # Configurar udev rules para dispositivos
            udev_rules = '''
# FruPrint Industrial - Reglas udev para dispositivos
SUBSYSTEM=="usb", ATTRS{idVendor}=="*", ATTRS{idProduct}=="*", MODE="0666"
KERNEL=="video[0-9]*", MODE="0666"
SUBSYSTEM=="gpio", MODE="0666"
SUBSYSTEM=="i2c-dev", MODE="0666"
SUBSYSTEM=="spi", MODE="0666"
'''
            
            rules_file = "/etc/udev/rules.d/99-fruprint.rules"
            try:
                with open("temp_udev_rules", "w") as f:
                    f.write(udev_rules)
                
                subprocess.run([
                    "sudo", "cp", "temp_udev_rules", rules_file
                ], capture_output=True, check=False)
                
                os.remove("temp_udev_rules")
                
                # Recargar reglas udev
                subprocess.run([
                    "sudo", "udevadm", "control", "--reload-rules"
                ], capture_output=True, check=False)
                
            except:
                pass
            
            logger.info("Permisos configurados")
            
        except Exception as e:
            logger.warning(f"Advertencia configurando permisos: {e}")
    
    def _validate_installation(self) -> bool:
        """Valida la instalación completa."""
        logger.info("Validando instalación...")
        
        try:
            # Obtener rutas del entorno virtual
            if self.system_info.platform == "windows":
                python_path = self.venv_path / "Scripts" / "python.exe"
            else:
                python_path = self.venv_path / "bin" / "python"
            
            # Verificar dependencias críticas
            critical_imports = [
                "torch", "torchvision", "ultralytics", "cv2", 
                "fastapi", "uvicorn", "pydantic", "numpy"
            ]
            
            for module in critical_imports:
                result = subprocess.run([
                    str(python_path), "-c", f"import {module}; print(f'{module} OK')"
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    logger.error(f"Módulo {module} no disponible: {result.stderr}")
                    return False
                else:
                    logger.info(f"✅ {module}")
            
            # Verificar configuración
            if not self.config_path.exists():
                logger.error("Configuración no encontrada")
                return False
            
            # Validar configuración
            from utils.config_validator import validate_config
            if not validate_config(str(self.config_path)):
                logger.error("Configuración inválida")
                return False
            
            logger.info("✅ Instalación validada")
            return True
            
        except Exception as e:
            logger.error(f"Error en validación: {e}")
            return False
    
    def _setup_services(self):
        """Configura servicios del sistema (opcional)."""
        logger.info("Configurando servicios del sistema...")
        
        if not self.system_info.is_raspberry_pi:
            logger.info("Servicios de sistema no configurados (no es Raspberry Pi)")
            return
        
        try:
            # Crear archivo de servicio systemd
            service_content = f'''[Unit]
Description=FruPrint Industrial System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory={self.project_root}
Environment=PATH={self.venv_path}/bin
ExecStart={self.venv_path}/bin/python main_etiquetadora.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
'''
            
            # Escribir archivo de servicio
            with open("fruprint.service", "w") as f:
                f.write(service_content)
            
            # Instalar servicio
            subprocess.run([
                "sudo", "cp", "fruprint.service", "/etc/systemd/system/"
            ], capture_output=True, check=False)
            
            # Habilitar servicio
            subprocess.run([
                "sudo", "systemctl", "enable", "fruprint.service"
            ], capture_output=True, check=False)
            
            os.remove("fruprint.service")
            
            logger.info("✅ Servicio systemd configurado")
            logger.info("Para iniciar: sudo systemctl start fruprint")
            logger.info("Para detener: sudo systemctl stop fruprint")
            logger.info("Ver logs: sudo journalctl -u fruprint -f")
            
        except Exception as e:
            logger.warning(f"Advertencia configurando servicio: {e}")
    
    def _print_next_steps(self):
        """Imprime los siguientes pasos para el usuario."""
        print("\\n" + "="*60)
        print("🎉 INSTALACIÓN COMPLETADA EXITOSAMENTE!")
        print("="*60)
        print("\\nPróximos pasos:")
        print("\\n1. Activar entorno virtual:")
        
        if self.system_info.platform == "windows":
            print(f"   .\\\\venv\\\\Scripts\\\\activate")
        else:
            print(f"   source venv/bin/activate")
        
        print("\\n2. Configurar hardware:")
        print("   - Conectar cámara")
        print("   - Conectar banda transportadora")
        print("   - Conectar sensores")
        print("   - Conectar actuador de etiquetado")
        
        print("\\n3. Configurar modelo de IA:")
        print("   - Colocar modelo entrenado en: IA_Etiquetado/Models/best_fruit_model.pt")
        print("   - O entrenar un nuevo modelo con su dataset")
        
        print("\\n4. Revisar configuración:")
        print(f"   - Editar: {self.config_path}")
        print("   - Ajustar parámetros según su hardware")
        
        print("\\n5. Ejecutar sistema:")
        print("   python main_etiquetadora.py")
        
        print("\\n6. Acceder a API web:")
        print("   http://localhost:8000/docs")
        
        if self.system_info.is_raspberry_pi:
            print("\\n7. Reiniciar Raspberry Pi:")
            print("   sudo reboot")
            print("   (Necesario para aplicar configuraciones GPIO)")
        
        print("\\n📚 Documentación completa en README.md")
        print("🆘 Soporte: Revisar logs en fruprint_install.log")
        print("="*60)


def main():
    """Función principal del instalador."""
    print("🍓 FruPrint Industrial v2.0 - Instalador Automatizado")
    print("=" * 55)
    
    # Verificar Python
    if sys.version_info < (3, 8):
        print(f"❌ Python 3.8+ requerido, encontrado {sys.version}")
        return 1
    
    # Verificar permisos en Linux
    if platform.system().lower() == "linux" and os.geteuid() == 0:
        print("❌ No ejecutar como root/sudo")
        print("💡 Ejecutar como usuario normal, sudo se usará cuando sea necesario")
        return 1
    
    try:
        installer = FruPrintInstaller()
        
        # Confirmar instalación
        response = input("\\n¿Continuar con la instalación? (s/N): ").lower().strip()
        if response not in ['s', 'si', 'sí', 'y', 'yes']:
            print("Instalación cancelada por el usuario")
            return 0
        
        # Ejecutar instalación
        success = installer.install()
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\\n❌ Instalación interrumpida por el usuario")
        return 1
    except Exception as e:
        logger.exception(f"Error fatal en instalador: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())