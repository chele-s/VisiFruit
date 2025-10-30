#!/usr/bin/env python3
"""Script de validación de seguridad para VisiFruit.

Verifica configuraciones críticas de seguridad antes del despliegue.
Autor: Gabriel Calderón, Elias Bautista
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple

class SecurityValidator:
    """Validador de configuración de seguridad."""
    
    def __init__(self):
        self.issues: List[str] = []
        self.warnings: List[str] = []
        self.passed: List[str] = []
        
    def validate_env_file(self) -> bool:
        """Valida archivo .env"""
        env_path = Path(".env")
        
        if not env_path.exists():
            self.issues.append("❌ Archivo .env no existe. Copia .env.example a .env")
            return False
        
        self.passed.append("✅ Archivo .env encontrado")
        
        # Leer contenido
        with open(env_path, 'r') as f:
            content = f.read()
        
        # Validar variables críticas
        required_vars = [
            "AUTH_TOKENS",
            "JWT_SECRET_KEY",
            "ALLOWED_ORIGINS"
        ]
        
        for var in required_vars:
            if f"{var}=" not in content:
                self.issues.append(f"❌ Variable {var} no configurada en .env")
            elif f"{var}=\n" in content or f"{var}=" in content and content.split(f"{var}=")[1].split("\n")[0].strip() == "":
                self.warnings.append(f"⚠️ Variable {var} está vacía")
            else:
                self.passed.append(f"✅ Variable {var} configurada")
        
        return True
    
    def validate_cors_config(self) -> bool:
        """Valida configuración CORS"""
        allowed_origins = os.getenv("ALLOWED_ORIGINS", "")
        
        if "*" in allowed_origins:
            self.issues.append("❌ CORS configurado con wildcard (*). Esto es INSEGURO para producción")
            return False
        
        if not allowed_origins:
            self.warnings.append("⚠️ ALLOWED_ORIGINS no configurado")
            return False
        
        self.passed.append(f"✅ CORS configurado con orígenes específicos: {allowed_origins}")
        return True
    
    def validate_auth_tokens(self) -> bool:
        """Valida tokens de autenticación"""
        tokens = os.getenv("AUTH_TOKENS", "")
        
        if not tokens:
            self.warnings.append("⚠️ AUTH_TOKENS no configurado. Autenticación deshabilitada")
            return False
        
        # Verificar tokens débiles conocidos
        weak_tokens = ["visifruittoken2025", "debugtoken", "test", "admin", "password"]
        token_list = [t.strip() for t in tokens.split(",")]
        
        for token in token_list:
            if token.lower() in weak_tokens:
                self.issues.append(f"❌ Token débil detectado: '{token}'. Usa tokens criptográficamente seguros")
                return False
            
            if len(token) < 20:
                self.warnings.append(f"⚠️ Token '{token[:5]}...' parece corto. Recomendado: 32+ caracteres")
        
        self.passed.append(f"✅ {len(token_list)} token(s) de autenticación configurados")
        return True
    
    def validate_jwt_secret(self) -> bool:
        """Valida JWT secret key"""
        jwt_secret = os.getenv("JWT_SECRET_KEY", "")
        
        if not jwt_secret:
            self.warnings.append("⚠️ JWT_SECRET_KEY no configurado. Se generará uno temporal")
            return False
        
        if len(jwt_secret) < 32:
            self.warnings.append("⚠️ JWT_SECRET_KEY parece corto. Recomendado: 64+ caracteres")
        
        # Verificar secretos débiles
        weak_secrets = ["secret", "password", "fruprint", "jwt_secret", "change_me"]
        if any(weak in jwt_secret.lower() for weak in weak_secrets):
            self.issues.append("❌ JWT_SECRET_KEY parece débil o predecible")
            return False
        
        self.passed.append("✅ JWT_SECRET_KEY configurado")
        return True
    
    def validate_admin_password(self) -> bool:
        """Valida contraseña de admin"""
        admin_pass = os.getenv("ADMIN_DEFAULT_PASSWORD", "")
        
        if not admin_pass:
            self.warnings.append("⚠️ ADMIN_DEFAULT_PASSWORD no configurado. Se generará uno aleatorio")
            return True  # No es crítico
        
        # Verificar contraseñas débiles
        weak_passwords = ["admin", "admin123", "password", "123456", "admin123456"]
        if admin_pass.lower() in weak_passwords:
            self.issues.append("❌ ADMIN_DEFAULT_PASSWORD es una contraseña débil conocida")
            return False
        
        if len(admin_pass) < 8:
            self.warnings.append("⚠️ ADMIN_DEFAULT_PASSWORD es corta. Recomendado: 12+ caracteres")
        
        self.passed.append("✅ ADMIN_DEFAULT_PASSWORD configurado")
        return True
    
    def validate_roboflow_key(self) -> bool:
        """Valida configuración de Roboflow"""
        model_type = os.getenv("MODEL_TYPE", "yolov8")
        
        if model_type == "roboflow":
            api_key = os.getenv("ROBOFLOW_API_KEY", "")
            project_id = os.getenv("ROBOFLOW_PROJECT_ID", "")
            
            if not api_key:
                self.issues.append("❌ MODEL_TYPE=roboflow pero ROBOFLOW_API_KEY no configurado")
                return False
            
            if not project_id:
                self.issues.append("❌ MODEL_TYPE=roboflow pero ROBOFLOW_PROJECT_ID no configurado")
                return False
            
            self.passed.append("✅ Configuración de Roboflow completa")
        
        return True
    
    def check_gitignore(self) -> bool:
        """Verifica que .env está en .gitignore"""
        gitignore_path = Path(".gitignore")
        
        if not gitignore_path.exists():
            self.warnings.append("⚠️ .gitignore no existe. Crea uno para evitar commits de .env")
            return False
        
        with open(gitignore_path, 'r') as f:
            content = f.read()
        
        if ".env" not in content:
            self.issues.append("❌ .env NO está en .gitignore. Riesgo de commit accidental")
            return False
        
        self.passed.append("✅ .env está en .gitignore")
        return True
    
    def check_file_permissions(self) -> bool:
        """Verifica permisos de archivos sensibles (solo Linux/Mac)"""
        if sys.platform.startswith('win'):
            self.warnings.append("ℹ️ Verificación de permisos omitida (Windows)")
            return True
        
        sensitive_files = [".env", "data/auth.db", "data/metrics.db"]
        
        for filepath in sensitive_files:
            path = Path(filepath)
            if path.exists():
                stat = path.stat()
                mode = stat.st_mode & 0o777
                
                if mode & 0o077:  # Otros usuarios tienen permisos
                    self.warnings.append(f"⚠️ {filepath} tiene permisos demasiado abiertos: {oct(mode)}")
        
        return True
    
    def run_all_checks(self) -> bool:
        """Ejecuta todas las validaciones"""
        print("=" * 60)
        print("🔒 VALIDADOR DE SEGURIDAD - VISIFRUIT")
        print("=" * 60)
        print()
        
        # Ejecutar validaciones
        checks = [
            ("Archivo .env", self.validate_env_file),
            ("Configuración CORS", self.validate_cors_config),
            ("Tokens de autenticación", self.validate_auth_tokens),
            ("JWT Secret Key", self.validate_jwt_secret),
            ("Contraseña de Admin", self.validate_admin_password),
            ("Roboflow API", self.validate_roboflow_key),
            (".gitignore", self.check_gitignore),
            ("Permisos de archivos", self.check_file_permissions),
        ]
        
        for name, check_func in checks:
            print(f"Validando {name}...", end=" ")
            try:
                check_func()
                print("✓")
            except Exception as e:
                print(f"✗ (Error: {e})")
                self.issues.append(f"❌ Error validando {name}: {e}")
        
        print()
        
        # Mostrar resultados
        if self.passed:
            print("✅ VERIFICACIONES PASADAS:")
            for item in self.passed:
                print(f"  {item}")
            print()
        
        if self.warnings:
            print("⚠️  ADVERTENCIAS:")
            for item in self.warnings:
                print(f"  {item}")
            print()
        
        if self.issues:
            print("❌ PROBLEMAS CRÍTICOS:")
            for item in self.issues:
                print(f"  {item}")
            print()
        
        # Resumen
        print("=" * 60)
        total = len(self.passed) + len(self.warnings) + len(self.issues)
        print(f"Resumen: {len(self.passed)} OK | {len(self.warnings)} Advertencias | {len(self.issues)} Críticos")
        print("=" * 60)
        
        if self.issues:
            print("⛔ HAY PROBLEMAS CRÍTICOS DE SEGURIDAD")
            print("   Por favor, corrígelos antes de desplegar a producción")
            return False
        elif self.warnings:
            print("⚠️  HAY ADVERTENCIAS DE SEGURIDAD")
            print("   Revisa las advertencias antes de desplegar a producción")
            return True
        else:
            print("✅ TODAS LAS VALIDACIONES PASARON")
            print("   El sistema está listo para despliegue seguro")
            return True

def main():
    """Función principal"""
    # Cargar .env si existe
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("⚠️ python-dotenv no instalado. Algunas validaciones pueden fallar")
        print("   Instala con: pip install python-dotenv")
        print()
    
    validator = SecurityValidator()
    success = validator.run_all_checks()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
