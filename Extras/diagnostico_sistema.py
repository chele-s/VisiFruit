#!/usr/bin/env python3
"""
Script de Diagnóstico del Sistema VisiFruit
============================================

Realiza verificaciones completas del sistema para identificar problemas
comunes antes de ejecutar los servicios.

Uso:
    python diagnostico_sistema.py [--detallado] [--fix]

Opciones:
    --detallado    Mostrar información detallada adicional
    --fix          Intentar reparar problemas automáticamente

Autor: Sistema VisiFruit
Fecha: 2025-08-12
"""

import argparse
import json
import os
import platform
import socket
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


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
            # En Windows, usar colores simples
            print(text)
        else:
            color_code = cls.COLORS.get(color, cls.COLORS['white'])
            bold_code = cls.COLORS['bold'] if bold else ''
            end_code = cls.COLORS['end']
            print(f"{bold_code}{color_code}{text}{end_code}")


class SistemaDiagnostico:
    """Diagnóstico completo del sistema VisiFruit."""
    
    def __init__(self, detallado: bool = False, fix: bool = False):
        self.detallado = detallado
        self.fix = fix
        self.problemas_encontrados = []
        self.advertencias = []
        self.fixes_aplicados = []
    
    def imprimir_cabecera(self):
        """Imprime cabecera del diagnóstico."""
        ColoredOutput.print("\n" + "="*60, 'cyan', True)
        ColoredOutput.print("    DIAGNÓSTICO DEL SISTEMA VISIFRUIT v3.0", 'cyan', True)
        ColoredOutput.print("="*60, 'cyan', True)
        ColoredOutput.print(f"Fecha: {Path(__file__).stat().st_mtime}", 'white')
        ColoredOutput.print(f"Plataforma: {platform.system()} {platform.release()}", 'white')
        ColoredOutput.print(f"Python: {sys.version.split()[0]}", 'white')
        print()
    
    def verificar_estructura_proyecto(self) -> bool:
        """Verifica la estructura básica del proyecto."""
        ColoredOutput.print("🔍 Verificando estructura del proyecto...", 'blue', True)
        
        archivos_criticos = [
            "main_etiquetadora.py",
            "Config_Etiquetadora.json",
            "Interfaz_Usuario/Backend/main.py"
        ]
        
        directorios_criticos = [
            "IA_Etiquetado",
            "Control_Etiquetado", 
            "Interfaz_Usuario/Backend",
            "data",
            "logs"
        ]
        
        todo_ok = True
        
        # Verificar archivos
        for archivo in archivos_criticos:
            if Path(archivo).exists():
                ColoredOutput.print(f"  ✅ {archivo}", 'green')
            else:
                ColoredOutput.print(f"  ❌ {archivo} - FALTANTE", 'red')
                self.problemas_encontrados.append(f"Archivo crítico faltante: {archivo}")
                todo_ok = False
        
        # Verificar directorios
        for directorio in directorios_criticos:
            path = Path(directorio)
            if path.exists():
                ColoredOutput.print(f"  ✅ {directorio}/", 'green')
                if self.fix and directorio == "logs" and not path.is_dir():
                    path.mkdir(parents=True, exist_ok=True)
                    self.fixes_aplicados.append(f"Creado directorio: {directorio}")
            else:
                if directorio in ["logs", "data"]:
                    ColoredOutput.print(f"  ⚠️  {directorio}/ - FALTANTE (se puede crear)", 'yellow')
                    self.advertencias.append(f"Directorio faltante: {directorio}")
                    if self.fix:
                        path.mkdir(parents=True, exist_ok=True)
                        ColoredOutput.print(f"     🔧 Directorio {directorio} creado", 'green')
                        self.fixes_aplicados.append(f"Creado directorio: {directorio}")
                else:
                    ColoredOutput.print(f"  ❌ {directorio}/ - FALTANTE", 'red')
                    self.problemas_encontrados.append(f"Directorio crítico faltante: {directorio}")
                    todo_ok = False
        
        print()
        return todo_ok
    
    def verificar_entorno_python(self) -> bool:
        """Verifica el entorno virtual y dependencias."""
        ColoredOutput.print("🐍 Verificando entorno Python...", 'blue', True)
        
        # Verificar entorno virtual
        venv_path = Path("venv")
        if venv_path.exists():
            ColoredOutput.print("  ✅ Entorno virtual existe", 'green')
            
            # Verificar ejecutable de Python
            if platform.system() == "Windows":
                python_exe = venv_path / "Scripts" / "python.exe"
            else:
                python_exe = venv_path / "bin" / "python"
            
            if python_exe.exists():
                ColoredOutput.print(f"  ✅ Python ejecutable: {python_exe}", 'green')
            else:
                ColoredOutput.print("  ❌ Ejecutable de Python no encontrado en venv", 'red')
                self.problemas_encontrados.append("Entorno virtual corrupto")
                return False
        else:
            ColoredOutput.print("  ❌ Entorno virtual no existe", 'red')
            self.problemas_encontrados.append("Entorno virtual faltante")
            if self.fix:
                ColoredOutput.print("     🔧 Creando entorno virtual...", 'yellow')
                try:
                    subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
                    ColoredOutput.print("     ✅ Entorno virtual creado", 'green')
                    self.fixes_aplicados.append("Creado entorno virtual")
                except subprocess.CalledProcessError as e:
                    ColoredOutput.print(f"     ❌ Error creando entorno virtual: {e}", 'red')
            return False
        
        # Verificar dependencias críticas
        try:
            import uvicorn, fastapi, numpy
            ColoredOutput.print("  ✅ Dependencias críticas instaladas", 'green')
        except ImportError as e:
            ColoredOutput.print(f"  ❌ Dependencias faltantes: {e}", 'red')
            self.problemas_encontrados.append(f"Dependencias faltantes: {e}")
            return False
        
        print()
        return True
    
    def verificar_configuracion(self) -> bool:
        """Verifica archivos de configuración."""
        ColoredOutput.print("⚙️  Verificando configuración...", 'blue', True)
        
        config_path = Path("Config_Etiquetadora.json")
        if not config_path.exists():
            ColoredOutput.print("  ❌ Config_Etiquetadora.json no existe", 'red')
            self.problemas_encontrados.append("Archivo de configuración principal faltante")
            return False
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            ColoredOutput.print("  ✅ Configuración principal válida", 'green')
            
            # Verificar puerto del sistema principal
            api_port = config.get("api_settings", {}).get("port", 8000)
            ColoredOutput.print(f"  ℹ️  Puerto sistema principal: {api_port}", 'white')
            
            if self.detallado:
                ColoredOutput.print("  📋 Configuraciones encontradas:", 'cyan')
                for seccion in config.keys():
                    ColoredOutput.print(f"     - {seccion}", 'white')
                    
        except json.JSONDecodeError as e:
            ColoredOutput.print(f"  ❌ Error en configuración JSON: {e}", 'red')
            self.problemas_encontrados.append(f"Configuración JSON inválida: {e}")
            return False
        except Exception as e:
            ColoredOutput.print(f"  ❌ Error leyendo configuración: {e}", 'red')
            self.problemas_encontrados.append(f"Error leyendo configuración: {e}")
            return False
        
        print()
        return True
    
    def verificar_puertos(self) -> bool:
        """Verifica disponibilidad de puertos críticos."""
        ColoredOutput.print("🔌 Verificando puertos críticos...", 'blue', True)
        
        puertos_criticos = {
            8000: "Sistema Principal",
            8001: "Backend Adicional", 
            3000: "Frontend React (dev)",
            5173: "Frontend React (Vite)"
        }
        
        puertos_ocupados = []
        
        for puerto, descripcion in puertos_criticos.items():
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(1)
                    result = sock.connect_ex(('localhost', puerto))
                    if result == 0:
                        ColoredOutput.print(f"  ⚠️  Puerto {puerto} ocupado - {descripcion}", 'yellow')
                        puertos_ocupados.append(puerto)
                        self.advertencias.append(f"Puerto {puerto} ocupado")
                    else:
                        ColoredOutput.print(f"  ✅ Puerto {puerto} libre - {descripcion}", 'green')
            except Exception as e:
                ColoredOutput.print(f"  ❓ Puerto {puerto} - Error verificando: {e}", 'yellow')
        
        if puertos_ocupados:
            ColoredOutput.print(f"\n  ⚠️  {len(puertos_ocupados)} puerto(s) ocupado(s)", 'yellow')
            ColoredOutput.print("     Esto puede causar conflictos al iniciar servicios", 'yellow')
        
        print()
        return len(puertos_ocupados) == 0
    
    def verificar_permisos(self) -> bool:
        """Verifica permisos de escritura en directorios críticos."""
        ColoredOutput.print("🔐 Verificando permisos...", 'blue', True)
        
        directorios_escritura = ["data", "logs", "temp"]
        todo_ok = True
        
        for directorio in directorios_escritura:
            path = Path(directorio)
            try:
                if not path.exists():
                    path.mkdir(parents=True, exist_ok=True)
                
                # Probar escritura
                test_file = path / ".test_write"
                test_file.write_text("test")
                test_file.unlink()
                
                ColoredOutput.print(f"  ✅ Permisos OK: {directorio}/", 'green')
            except Exception as e:
                ColoredOutput.print(f"  ❌ Sin permisos de escritura: {directorio}/ - {e}", 'red')
                self.problemas_encontrados.append(f"Sin permisos en directorio: {directorio}")
                todo_ok = False
        
        print()
        return todo_ok
    
    def generar_reporte(self) -> Dict:
        """Genera reporte completo del diagnóstico."""
        ColoredOutput.print("📊 Resumen del Diagnóstico", 'cyan', True)
        ColoredOutput.print("-" * 40, 'cyan')
        
        # Problemas críticos
        if self.problemas_encontrados:
            ColoredOutput.print(f"❌ PROBLEMAS CRÍTICOS ({len(self.problemas_encontrados)}):", 'red', True)
            for problema in self.problemas_encontrados:
                ColoredOutput.print(f"   • {problema}", 'red')
            print()
        
        # Advertencias
        if self.advertencias:
            ColoredOutput.print(f"⚠️  ADVERTENCIAS ({len(self.advertencias)}):", 'yellow', True)
            for advertencia in self.advertencias:
                ColoredOutput.print(f"   • {advertencia}", 'yellow')
            print()
        
        # Fixes aplicados
        if self.fixes_aplicados:
            ColoredOutput.print(f"🔧 FIXES APLICADOS ({len(self.fixes_aplicados)}):", 'green', True)
            for fix in self.fixes_aplicados:
                ColoredOutput.print(f"   • {fix}", 'green')
            print()
        
        # Estado general
        if not self.problemas_encontrados:
            ColoredOutput.print("🎉 SISTEMA LISTO PARA EJECUTAR", 'green', True)
            ColoredOutput.print("   Todos los componentes críticos verificados exitosamente", 'green')
        else:
            ColoredOutput.print("🚨 SISTEMA NO LISTO", 'red', True)
            ColoredOutput.print("   Resuelve los problemas críticos antes de continuar", 'red')
        
        return {
            'timestamp': Path(__file__).stat().st_mtime,
            'problemas_criticos': len(self.problemas_encontrados),
            'advertencias': len(self.advertencias),
            'fixes_aplicados': len(self.fixes_aplicados),
            'sistema_listo': len(self.problemas_encontrados) == 0
        }
    
    def ejecutar_diagnostico_completo(self) -> bool:
        """Ejecuta diagnóstico completo del sistema."""
        self.imprimir_cabecera()
        
        # Ejecutar todas las verificaciones
        verificaciones = [
            self.verificar_estructura_proyecto,
            self.verificar_entorno_python,
            self.verificar_configuracion,
            self.verificar_puertos,
            self.verificar_permisos
        ]
        
        resultados = []
        for verificacion in verificaciones:
            try:
                resultado = verificacion()
                resultados.append(resultado)
            except Exception as e:
                ColoredOutput.print(f"❌ Error en verificación: {e}", 'red')
                resultados.append(False)
        
        # Generar reporte final
        reporte = self.generar_reporte()
        
        return reporte['sistema_listo']


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Diagnóstico completo del sistema VisiFruit"
    )
    parser.add_argument(
        '--detallado', 
        action='store_true', 
        help='Mostrar información detallada adicional'
    )
    parser.add_argument(
        '--fix', 
        action='store_true', 
        help='Intentar reparar problemas automáticamente'
    )
    
    args = parser.parse_args()
    
    # Ejecutar diagnóstico
    diagnostico = SistemaDiagnostico(detallado=args.detallado, fix=args.fix)
    sistema_listo = diagnostico.ejecutar_diagnostico_completo()
    
    print()
    ColoredOutput.print("="*60, 'cyan')
    
    # Código de salida
    return 0 if sistema_listo else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        ColoredOutput.print("\n⚠️ Diagnóstico interrumpido por el usuario", 'yellow')
        sys.exit(1)
    except Exception as e:
        ColoredOutput.print(f"\n❌ Error inesperado: {e}", 'red')
        sys.exit(1)
