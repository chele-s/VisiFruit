#!/usr/bin/env python3
"""
Script de Migración FruPrint v3.0 → v4.0
========================================

Este script automatiza la migración del sistema monolítico v3.0
a la arquitectura modular v4.0.

Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Septiembre 2025
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime

# Colores para terminal
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKBLUE}ℹ️  {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

def check_prerequisites():
    """Verifica que todos los archivos necesarios existan."""
    print_info("Verificando prerrequisitos...")
    
    required_files = [
        "system_types.py",
        "metrics_system.py",
        "optimization_engine.py",
        "ultra_labeling_system.py",
        "database_manager.py",
        "service_manager.py",
        "system_utils.py",
        "ultra_api.py",
        "main_etiquetadora_v4.py",
        "main_etiquetadora.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print_error("Archivos faltantes:")
        for file in missing_files:
            print(f"  - {file}")
        return False
    
    print_success("Todos los archivos necesarios están presentes")
    return True

def create_backup():
    """Crea un backup del sistema v3.0."""
    print_info("Creando backup del sistema v3.0...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path(f"backup_v3_{timestamp}")
    
    try:
        backup_dir.mkdir(exist_ok=True)
        
        # Backup del archivo principal
        shutil.copy2("main_etiquetadora.py", backup_dir / "main_etiquetadora_v3.py")
        
        # Backup de configuración si existe
        if Path("Config_Etiquetadora.json").exists():
            shutil.copy2("Config_Etiquetadora.json", backup_dir / "Config_Etiquetadora.json")
        
        print_success(f"Backup creado en: {backup_dir}")
        return backup_dir
    except Exception as e:
        print_error(f"Error creando backup: {e}")
        return None

def perform_migration():
    """Realiza la migración de v3.0 a v4.0."""
    print_info("Iniciando migración...")
    
    try:
        # 1. Renombrar archivo original
        if Path("main_etiquetadora.py").exists():
            shutil.move("main_etiquetadora.py", "main_etiquetadora_v3.py")
            print_success("Archivo v3.0 renombrado a main_etiquetadora_v3.py")
        
        # 2. Copiar nuevo archivo principal
        shutil.copy2("main_etiquetadora_v4.py", "main_etiquetadora.py")
        print_success("Nuevo archivo v4.0 establecido como principal")
        
        # 3. Verificar módulos en su lugar
        modules = [
            "system_types.py",
            "metrics_system.py",
            "optimization_engine.py",
            "ultra_labeling_system.py",
            "database_manager.py",
            "service_manager.py",
            "system_utils.py",
            "ultra_api.py"
        ]
        
        print_info("Verificando módulos...")
        for module in modules:
            if Path(module).exists():
                print_success(f"  {module} ✓")
            else:
                print_error(f"  {module} ✗")
                return False
        
        return True
        
    except Exception as e:
        print_error(f"Error durante migración: {e}")
        return False

def rollback_migration(backup_dir):
    """Revierte la migración en caso de error."""
    print_warning("Revertiendo migración...")
    
    try:
        if backup_dir and backup_dir.exists():
            # Restaurar archivo original
            backup_file = backup_dir / "main_etiquetadora_v3.py"
            if backup_file.exists():
                shutil.copy2(backup_file, "main_etiquetadora.py")
                print_success("Archivo original restaurado")
            
            # Eliminar archivo v3 renombrado si existe
            if Path("main_etiquetadora_v3.py").exists():
                Path("main_etiquetadora_v3.py").unlink()
        
        print_success("Rollback completado")
        return True
    except Exception as e:
        print_error(f"Error en rollback: {e}")
        return False

def verify_migration():
    """Verifica que la migración fue exitosa."""
    print_info("Verificando migración...")
    
    checks = []
    
    # Verificar que el archivo principal es v4
    with open("main_etiquetadora.py", 'r', encoding='utf-8') as f:
        content = f.read()
        is_v4 = "v4.0" in content and "MODULAR ARCHITECTURE" in content
        checks.append(("Archivo principal es v4.0", is_v4))
    
    # Verificar que todos los módulos están presentes
    modules = [
        "system_types.py",
        "metrics_system.py",
        "optimization_engine.py",
        "ultra_labeling_system.py",
        "database_manager.py",
        "service_manager.py",
        "system_utils.py",
        "ultra_api.py"
    ]
    
    all_modules_present = all(Path(m).exists() for m in modules)
    checks.append(("Todos los módulos presentes", all_modules_present))
    
    # Verificar que el backup existe
    backup_exists = any(p.name.startswith("backup_v3_") for p in Path(".").iterdir() if p.is_dir())
    checks.append(("Backup creado", backup_exists))
    
    # Mostrar resultados
    print()
    for check_name, passed in checks:
        if passed:
            print_success(f"{check_name}")
        else:
            print_error(f"{check_name}")
    
    return all(passed for _, passed in checks)

def print_next_steps():
    """Imprime los próximos pasos después de la migración."""
    print_header("Próximos Pasos")
    
    steps = [
        "1. Revisa la documentación en ARCHITECTURE_V4.md",
        "2. Verifica que Config_Etiquetadora.json tiene todas las configuraciones",
        "3. Ejecuta el sistema con: python main_etiquetadora.py",
        "4. Verifica que todos los servicios inicien correctamente",
        "5. Prueba los endpoints de API en http://localhost:8000/docs",
        "6. Si hay problemas, restaura el backup desde backup_v3_XXXXXX/"
    ]
    
    for step in steps:
        print(f"  {Colors.OKCYAN}{step}{Colors.ENDC}")
    
    print()

def main():
    """Función principal del script de migración."""
    print_header("FruPrint Migration v3.0 → v4.0")
    
    print(f"{Colors.BOLD}Este script migrará tu sistema a la arquitectura modular v4.0{Colors.ENDC}")
    print()
    
    # Verificar prerrequisitos
    if not check_prerequisites():
        print_error("No se pueden cumplir los prerrequisitos")
        sys.exit(1)
    
    # Confirmar con usuario
    response = input(f"{Colors.WARNING}¿Deseas continuar con la migración? (s/n): {Colors.ENDC}").lower()
    if response not in ['s', 'si', 'y', 'yes']:
        print_info("Migración cancelada por el usuario")
        sys.exit(0)
    
    # Crear backup
    backup_dir = create_backup()
    if not backup_dir:
        print_error("No se pudo crear backup. Abortando migración.")
        sys.exit(1)
    
    # Realizar migración
    print()
    print_header("Migrando Sistema")
    
    if not perform_migration():
        print_error("La migración falló")
        rollback_migration(backup_dir)
        sys.exit(1)
    
    # Verificar migración
    print()
    if not verify_migration():
        print_warning("Algunas verificaciones fallaron")
        response = input(f"{Colors.WARNING}¿Deseas revertir la migración? (s/n): {Colors.ENDC}").lower()
        if response in ['s', 'si', 'y', 'yes']:
            rollback_migration(backup_dir)
            sys.exit(1)
    
    # Éxito
    print()
    print_header("¡Migración Completada! 🎉")
    print_success("Tu sistema ha sido actualizado a v4.0 exitosamente")
    print()
    
    print_next_steps()
    
    print(f"\n{Colors.BOLD}Backup guardado en: {backup_dir}{Colors.ENDC}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_warning("Migración interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        print()
        print_error(f"Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
