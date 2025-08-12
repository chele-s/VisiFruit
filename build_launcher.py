#!/usr/bin/env python3
"""
Script para compilar el VisiFruit Launcher a .exe
==================================================

Este script usa PyInstaller para crear un ejecutable de Windows
del launcher con todas las dependencias incluidas.

Uso:
    python build_launcher.py

Opciones:
    --debug: Compila con ventana de consola para debugging
    --onefile: Crea un solo archivo .exe (más lento al iniciar)
    --windowed: Sin ventana de consola (solo GUI)
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
import shutil

def check_dependencies():
    """Verifica que PyInstaller esté instalado"""
    try:
        import PyInstaller
        print("✅ PyInstaller encontrado")
        return True
    except ImportError:
        print("❌ PyInstaller no está instalado")
        print("Instala con: pip install pyinstaller")
        return False

def check_launcher_exists():
    """Verifica que el archivo del launcher exista"""
    launcher_file = Path("visifruit_launcher.py")
    if launcher_file.exists():
        print("✅ Archivo launcher encontrado")
        return True
    else:
        print("❌ No se encuentra visifruit_launcher.py")
        return False

def create_icon():
    """Crea un archivo .ico si es posible desde las imágenes disponibles"""
    logo_path = Path("Others/Images/VisiFruit Logo.png")
    if logo_path.exists():
        try:
            from PIL import Image
            # Convertir PNG a ICO
            img = Image.open(logo_path)
            ico_path = Path("visifruit_icon.ico")
            img.save(ico_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
            print(f"✅ Icono creado: {ico_path}")
            return str(ico_path)
        except Exception as e:
            print(f"⚠️ No se pudo crear icono: {e}")
            return None
    return None

def build_launcher(args):
    """Compila el launcher usando PyInstaller"""
    print("🚀 Iniciando compilación del VisiFruit Launcher...")
    
    # Comando base de PyInstaller
    cmd = [
        "pyinstaller",
        "--name=VisiFruit_Launcher",
        "--distpath=dist",
        "--workpath=build_temp",
        "--specpath=build_specs"
    ]
    
    # Opciones según argumentos
    if args.onefile:
        cmd.append("--onefile")
        print("📦 Modo: Un solo archivo .exe")
    else:
        cmd.append("--onedir")
        print("📁 Modo: Directorio con dependencias")
    
    if args.windowed:
        cmd.append("--windowed")
        print("🪟 Modo: Solo ventana GUI (sin consola)")
    elif not args.debug:
        cmd.append("--noconsole")
        print("🔇 Modo: Sin ventana de consola")
    else:
        print("🐛 Modo: Con ventana de consola (debug)")
    
    # Agregar icono si existe
    icon_path = create_icon()
    if icon_path:
        cmd.extend(["--icon", icon_path])
    
    # Incluir archivos adicionales
    cmd.extend([
        "--add-data", "start_sistema_completo.bat;.",
        "--add-data", "start_sistema_completo.ps1;.",
        "--add-data", "start_backend.bat;.",
        "--add-data", "start_frontend.bat;.",
    ])
    
    # Verificar si existen archivos de configuración
    config_files = [
        "Config_Etiquetadora.json",
        "launcher_requirements.txt"
    ]
    
    for config_file in config_files:
        if Path(config_file).exists():
            cmd.extend(["--add-data", f"{config_file};."])
    
    # Incluir logos si existen
    if Path("Others/Images").exists():
        cmd.extend(["--add-data", "Others/Images;Others/Images"])
    
    # Archivo principal
    cmd.append("visifruit_launcher.py")
    
    print(f"🔧 Comando PyInstaller: {' '.join(cmd)}")
    print()
    
    try:
        # Ejecutar PyInstaller
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        print("✅ Compilación exitosa!")
        print()
        
        # Mostrar información del resultado
        if args.onefile:
            exe_path = Path("dist/VisiFruit_Launcher.exe")
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print(f"📄 Archivo generado: {exe_path}")
                print(f"📏 Tamaño: {size_mb:.1f} MB")
            else:
                print("⚠️ No se encontró el archivo .exe generado")
        else:
            dist_dir = Path("dist/VisiFruit_Launcher")
            if dist_dir.exists():
                exe_path = dist_dir / "VisiFruit_Launcher.exe"
                if exe_path.exists():
                    print(f"📁 Directorio generado: {dist_dir}")
                    print(f"📄 Ejecutable: {exe_path}")
                    
                    # Contar archivos
                    file_count = len(list(dist_dir.rglob("*")))
                    print(f"📊 Archivos totales: {file_count}")
        
        print()
        print("🎉 ¡Launcher compilado exitosamente!")
        print("💡 Ahora puedes distribuir el archivo .exe o carpeta completa")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error durante la compilación:")
        print(f"Código de salida: {e.returncode}")
        print(f"Salida: {e.stdout}")
        print(f"Error: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def cleanup_build_files():
    """Limpia archivos temporales de compilación"""
    cleanup_dirs = ["build_temp", "build_specs", "__pycache__"]
    cleanup_files = ["visifruit_icon.ico"]
    
    for dir_name in cleanup_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            try:
                shutil.rmtree(dir_path)
                print(f"🧹 Eliminado: {dir_path}")
            except Exception as e:
                print(f"⚠️ No se pudo eliminar {dir_path}: {e}")
    
    for file_name in cleanup_files:
        file_path = Path(file_name)
        if file_path.exists():
            try:
                file_path.unlink()
                print(f"🧹 Eliminado: {file_path}")
            except Exception as e:
                print(f"⚠️ No se pudo eliminar {file_path}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Compila el VisiFruit Launcher a .exe")
    parser.add_argument("--debug", action="store_true", 
                       help="Compila con ventana de consola para debugging")
    parser.add_argument("--onefile", action="store_true",
                       help="Crea un solo archivo .exe")
    parser.add_argument("--windowed", action="store_true",
                       help="Sin ventana de consola (solo GUI)")
    parser.add_argument("--cleanup", action="store_true",
                       help="Limpiar archivos temporales después de compilar")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🍎 VisiFruit Launcher - Constructor de Ejecutable")
    print("=" * 60)
    print()
    
    # Verificaciones previas
    if not check_dependencies():
        sys.exit(1)
    
    if not check_launcher_exists():
        sys.exit(1)
    
    # Compilar
    success = build_launcher(args)
    
    # Limpiar si se solicita
    if args.cleanup:
        print()
        print("🧹 Limpiando archivos temporales...")
        cleanup_build_files()
    
    if success:
        print()
        print("🎊 ¡Proceso completado exitosamente!")
        print("📋 Instrucciones de uso:")
        print("   1. Navega a la carpeta 'dist'")
        print("   2. Ejecuta 'VisiFruit_Launcher.exe'")
        print("   3. ¡Disfruta de tu launcher visual!")
        sys.exit(0)
    else:
        print()
        print("💥 La compilación falló. Revisa los errores anteriores.")
        sys.exit(1)

if __name__ == "__main__":
    main()
