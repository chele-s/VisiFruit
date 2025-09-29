# backup_manager.py
"""
Sistema de Respaldo Automático FruPrint v4.0
============================================

Sistema de backup automático con rotación, compresión
y restauración de configuraciones y datos.

Características:
- Backup automático programado
- Compresión de backups
- Rotación automática de backups antiguos
- Backup incremental
- Restauración de backups
- Verificación de integridad

Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Septiembre 2025
Versión: 4.0 - MODULAR ARCHITECTURE
"""

import asyncio
import logging
import shutil
import gzip
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class BackupInfo:
    """Información de un backup."""
    backup_id: str
    timestamp: datetime
    backup_type: str  # 'full' or 'incremental'
    files_backed_up: List[str]
    size_bytes: int
    compressed: bool
    checksum: str
    backup_path: Path
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['backup_path'] = str(self.backup_path)
        return data

class BackupManager:
    """Gestor de backups automáticos del sistema."""
    
    def __init__(self, backup_dir: Optional[Path] = None):
        """
        Inicializa el gestor de backups.
        
        Args:
            backup_dir: Directorio para almacenar backups
        """
        self.backup_dir = backup_dir or Path("data") / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Índice de backups
        self.backup_index_file = self.backup_dir / "backup_index.json"
        self.backup_index: List[BackupInfo] = []
        
        # Configuración
        self.config = {
            "auto_backup_enabled": True,
            "backup_interval_hours": 24,
            "max_backups": 30,
            "compress_backups": True,
            "include_logs": False,
            "backup_types": ["database", "config", "metrics"]
        }
        
        # Estado
        self.running = False
        self.last_backup_time: Optional[datetime] = None
        
        # Cargar índice
        self._load_index()
    
    def _load_index(self):
        """Carga el índice de backups."""
        try:
            if self.backup_index_file.exists():
                with open(self.backup_index_file, 'r') as f:
                    data = json.load(f)
                    self.backup_index = [
                        BackupInfo(
                            backup_id=item['backup_id'],
                            timestamp=datetime.fromisoformat(item['timestamp']),
                            backup_type=item['backup_type'],
                            files_backed_up=item['files_backed_up'],
                            size_bytes=item['size_bytes'],
                            compressed=item['compressed'],
                            checksum=item['checksum'],
                            backup_path=Path(item['backup_path'])
                        )
                        for item in data
                    ]
                logger.info(f"✅ Índice de backups cargado: {len(self.backup_index)} backups")
        except Exception as e:
            logger.error(f"Error cargando índice de backups: {e}")
            self.backup_index = []
    
    def _save_index(self):
        """Guarda el índice de backups."""
        try:
            with open(self.backup_index_file, 'w') as f:
                json.dump([b.to_dict() for b in self.backup_index], f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error guardando índice de backups: {e}")
    
    async def start_auto_backup(self):
        """Inicia el sistema de backup automático."""
        self.running = True
        logger.info("💾 Sistema de backup automático iniciado")
        
        while self.running:
            try:
                # Verificar si es necesario hacer backup
                if self._should_backup():
                    logger.info("🔄 Iniciando backup automático...")
                    await self.create_backup(backup_type="full")
                
                # Esperar al siguiente ciclo
                await asyncio.sleep(3600)  # Verificar cada hora
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error en backup automático: {e}")
                await asyncio.sleep(3600)
    
    def stop_auto_backup(self):
        """Detiene el sistema de backup automático."""
        self.running = False
        logger.info("🛑 Sistema de backup automático detenido")
    
    def _should_backup(self) -> bool:
        """Determina si es necesario crear un backup."""
        if not self.config["auto_backup_enabled"]:
            return False
        
        if self.last_backup_time is None:
            return True
        
        hours_since_last = (datetime.now() - self.last_backup_time).total_seconds() / 3600
        return hours_since_last >= self.config["backup_interval_hours"]
    
    async def create_backup(self, backup_type: str = "full") -> Optional[BackupInfo]:
        """
        Crea un nuevo backup del sistema.
        
        Args:
            backup_type: Tipo de backup ('full' o 'incremental')
        
        Returns:
            Información del backup creado
        """
        try:
            timestamp = datetime.now()
            backup_id = f"backup_{timestamp.strftime('%Y%m%d_%H%M%S')}"
            
            logger.info(f"📦 Creando backup {backup_type}: {backup_id}")
            
            # Crear directorio para este backup
            backup_path = self.backup_dir / backup_id
            backup_path.mkdir(exist_ok=True)
            
            # Archivos a respaldar
            files_backed_up = []
            
            # 1. Base de datos
            if "database" in self.config["backup_types"]:
                db_files = await self._backup_database(backup_path)
                files_backed_up.extend(db_files)
            
            # 2. Configuración
            if "config" in self.config["backup_types"]:
                config_files = await self._backup_configs(backup_path)
                files_backed_up.extend(config_files)
            
            # 3. Logs (opcional)
            if self.config["include_logs"] and "logs" in self.config["backup_types"]:
                log_files = await self._backup_logs(backup_path)
                files_backed_up.extend(log_files)
            
            # Comprimir si está habilitado
            if self.config["compress_backups"]:
                compressed_path = await self._compress_backup(backup_path)
                # Eliminar carpeta sin comprimir
                shutil.rmtree(backup_path)
                final_path = compressed_path
            else:
                final_path = backup_path
            
            # Calcular checksum
            checksum = await self._calculate_checksum(final_path)
            
            # Calcular tamaño total
            if final_path.is_file():
                size_bytes = final_path.stat().st_size
            else:
                size_bytes = sum(f.stat().st_size for f in final_path.rglob('*') if f.is_file())
            
            # Crear info del backup
            backup_info = BackupInfo(
                backup_id=backup_id,
                timestamp=timestamp,
                backup_type=backup_type,
                files_backed_up=files_backed_up,
                size_bytes=size_bytes,
                compressed=self.config["compress_backups"],
                checksum=checksum,
                backup_path=final_path
            )
            
            # Agregar al índice
            self.backup_index.append(backup_info)
            self._save_index()
            
            # Actualizar último backup
            self.last_backup_time = timestamp
            
            # Limpiar backups antiguos
            await self._cleanup_old_backups()
            
            size_mb = size_bytes / (1024 ** 2)
            logger.info(f"✅ Backup creado: {backup_id} ({size_mb:.2f} MB)")
            
            return backup_info
            
        except Exception as e:
            logger.error(f"❌ Error creando backup: {e}")
            return None
    
    async def _backup_database(self, backup_path: Path) -> List[str]:
        """Respalda la base de datos."""
        files = []
        db_file = Path("data") / "fruprint_ultra.db"
        
        if db_file.exists():
            dest = backup_path / "database"
            dest.mkdir(exist_ok=True)
            
            shutil.copy2(db_file, dest / db_file.name)
            files.append(str(db_file))
            logger.debug(f"  ✓ Base de datos respaldada")
        
        return files
    
    async def _backup_configs(self, backup_path: Path) -> List[str]:
        """Respalda archivos de configuración."""
        files = []
        config_files = [
            "Config_Etiquetadora.json",
            "Prototipo_Clasificador/Config_Prototipo.json"
        ]
        
        dest = backup_path / "configs"
        dest.mkdir(exist_ok=True)
        
        for config_file in config_files:
            source = Path(config_file)
            if source.exists():
                target = dest / source.name
                shutil.copy2(source, target)
                files.append(config_file)
        
        logger.debug(f"  ✓ {len(files)} archivos de configuración respaldados")
        return files
    
    async def _backup_logs(self, backup_path: Path) -> List[str]:
        """Respalda logs del sistema."""
        files = []
        log_dir = Path("logs")
        
        if log_dir.exists():
            dest = backup_path / "logs"
            dest.mkdir(exist_ok=True)
            
            # Copiar solo logs recientes (últimos 7 días)
            cutoff_date = datetime.now() - timedelta(days=7)
            
            for log_file in log_dir.rglob("*.log"):
                if log_file.stat().st_mtime > cutoff_date.timestamp():
                    rel_path = log_file.relative_to(log_dir)
                    target = dest / rel_path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(log_file, target)
                    files.append(str(log_file))
            
            logger.debug(f"  ✓ {len(files)} archivos de log respaldados")
        
        return files
    
    async def _compress_backup(self, backup_path: Path) -> Path:
        """Comprime un backup."""
        try:
            compressed_path = backup_path.with_suffix('.tar.gz')
            
            # Crear archivo tar.gz
            import tarfile
            with tarfile.open(compressed_path, 'w:gz') as tar:
                tar.add(backup_path, arcname=backup_path.name)
            
            logger.debug(f"  ✓ Backup comprimido: {compressed_path.name}")
            return compressed_path
            
        except Exception as e:
            logger.error(f"Error comprimiendo backup: {e}")
            return backup_path
    
    async def _calculate_checksum(self, file_path: Path) -> str:
        """Calcula checksum MD5 de un archivo."""
        try:
            md5 = hashlib.md5()
            
            if file_path.is_file():
                with open(file_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        md5.update(chunk)
            else:
                # Para directorios, calcular checksum de todos los archivos
                for file in sorted(file_path.rglob('*')):
                    if file.is_file():
                        with open(file, 'rb') as f:
                            for chunk in iter(lambda: f.read(4096), b""):
                                md5.update(chunk)
            
            return md5.hexdigest()
            
        except Exception as e:
            logger.error(f"Error calculando checksum: {e}")
            return "unknown"
    
    async def _cleanup_old_backups(self):
        """Limpia backups antiguos según la política de retención."""
        try:
            if len(self.backup_index) <= self.config["max_backups"]:
                return
            
            # Ordenar por fecha (más antiguo primero)
            sorted_backups = sorted(self.backup_index, key=lambda b: b.timestamp)
            
            # Eliminar los más antiguos
            to_delete = sorted_backups[:len(sorted_backups) - self.config["max_backups"]]
            
            for backup in to_delete:
                try:
                    if backup.backup_path.exists():
                        if backup.backup_path.is_file():
                            backup.backup_path.unlink()
                        else:
                            shutil.rmtree(backup.backup_path)
                    
                    self.backup_index.remove(backup)
                    logger.debug(f"  Backup antiguo eliminado: {backup.backup_id}")
                except Exception as e:
                    logger.error(f"Error eliminando backup {backup.backup_id}: {e}")
            
            self._save_index()
            logger.info(f"🧹 {len(to_delete)} backups antiguos eliminados")
            
        except Exception as e:
            logger.error(f"Error en limpieza de backups: {e}")
    
    async def restore_backup(self, backup_id: str) -> bool:
        """
        Restaura un backup.
        
        Args:
            backup_id: ID del backup a restaurar
        
        Returns:
            True si la restauración fue exitosa
        """
        try:
            # Buscar backup
            backup = next((b for b in self.backup_index if b.backup_id == backup_id), None)
            
            if not backup:
                logger.error(f"Backup no encontrado: {backup_id}")
                return False
            
            logger.info(f"🔄 Restaurando backup: {backup_id}")
            
            # Verificar checksum
            current_checksum = await self._calculate_checksum(backup.backup_path)
            if current_checksum != backup.checksum:
                logger.error("❌ Checksum no coincide - backup corrupto")
                return False
            
            # Descomprimir si es necesario
            if backup.compressed:
                extract_path = self.backup_dir / f"restore_{backup_id}"
                await self._extract_backup(backup.backup_path, extract_path)
                source_path = extract_path
            else:
                source_path = backup.backup_path
            
            # Restaurar archivos
            # Base de datos
            db_backup = source_path / "database" / "fruprint_ultra.db"
            if db_backup.exists():
                db_dest = Path("data") / "fruprint_ultra.db"
                # Backup actual antes de sobrescribir
                if db_dest.exists():
                    shutil.copy2(db_dest, db_dest.with_suffix('.db.before_restore'))
                shutil.copy2(db_backup, db_dest)
                logger.info("  ✓ Base de datos restaurada")
            
            # Configs
            configs_backup = source_path / "configs"
            if configs_backup.exists():
                for config_file in configs_backup.iterdir():
                    # Determinar destino basándose en el nombre
                    if config_file.name == "Config_Prototipo.json":
                        dest = Path("Prototipo_Clasificador") / config_file.name
                    else:
                        dest = Path(config_file.name)
                    
                    # Backup antes de sobrescribir
                    if dest.exists():
                        shutil.copy2(dest, dest.with_suffix(dest.suffix + '.before_restore'))
                    
                    shutil.copy2(config_file, dest)
                logger.info("  ✓ Configuraciones restauradas")
            
            # Limpiar directorio temporal
            if backup.compressed and extract_path.exists():
                shutil.rmtree(extract_path)
            
            logger.info(f"✅ Backup restaurado exitosamente: {backup_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error restaurando backup: {e}")
            return False
    
    async def _extract_backup(self, compressed_file: Path, extract_path: Path):
        """Extrae un backup comprimido."""
        import tarfile
        
        extract_path.mkdir(exist_ok=True)
        
        with tarfile.open(compressed_file, 'r:gz') as tar:
            tar.extractall(extract_path)
        
        logger.debug(f"  ✓ Backup extraído a: {extract_path}")
    
    def get_backup_list(self) -> List[Dict[str, Any]]:
        """Obtiene la lista de backups disponibles."""
        return [
            {
                "backup_id": b.backup_id,
                "timestamp": b.timestamp.isoformat(),
                "backup_type": b.backup_type,
                "size_mb": round(b.size_bytes / (1024 ** 2), 2),
                "compressed": b.compressed,
                "files_count": len(b.files_backed_up)
            }
            for b in sorted(self.backup_index, key=lambda x: x.timestamp, reverse=True)
        ]
    
    def get_backup_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de backups."""
        if not self.backup_index:
            return {
                "total_backups": 0,
                "total_size_mb": 0,
                "oldest_backup": None,
                "newest_backup": None
            }
        
        total_size = sum(b.size_bytes for b in self.backup_index)
        sorted_backups = sorted(self.backup_index, key=lambda b: b.timestamp)
        
        return {
            "total_backups": len(self.backup_index),
            "total_size_mb": round(total_size / (1024 ** 2), 2),
            "oldest_backup": sorted_backups[0].timestamp.isoformat(),
            "newest_backup": sorted_backups[-1].timestamp.isoformat(),
            "last_backup": self.last_backup_time.isoformat() if self.last_backup_time else None,
            "auto_backup_enabled": self.config["auto_backup_enabled"]
        }

__all__ = ['BackupManager', 'BackupInfo']
