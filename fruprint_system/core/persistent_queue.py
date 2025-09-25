# fruprint_system/core/persistent_queue.py
import asyncio
import pickle
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class PersistentQueue:
    """
    Una cola de asyncio que guarda su estado en un archivo para
    recuperarlo después de un reinicio.
    """
    def __init__(self, backup_path: str = "queue_backup.pkl"):
        self.path = Path(backup_path)
        self.queue = asyncio.Queue()
        self._load_from_backup()

    def _load_from_backup(self):
        """Carga la cola desde el archivo de respaldo si existe."""
        if self.path.exists():
            try:
                with open(self.path, 'rb') as f:
                    items = pickle.load(f)
                    for item in items:
                        self.queue.put_nowait(item)
                logger.info(f"Se cargaron {len(items)} elementos desde el respaldo de la cola.")
            except (pickle.UnpicklingError, EOFError) as e:
                logger.warning(f"No se pudo cargar el respaldo de la cola ({e}). Empezando con una cola vacía.")
            finally:
                self.path.unlink() # Borrar el respaldo después de intentar cargarlo

    def backup_to_file(self):
        """Guarda los elementos actuales de la cola en un archivo."""
        if self.queue.empty():
            return
        
        items = []
        while not self.queue.empty():
            items.append(self.queue.get_nowait())
        
        try:
            with open(self.path, 'wb') as f:
                pickle.dump(items, f)
            logger.info(f"Se respaldaron {len(items)} elementos de la cola en '{self.path}'.")
        except pickle.PicklingError as e:
            logger.error(f"Error al respaldar la cola: {e}")

    # --- Métodos de la interfaz de asyncio.Queue ---

    async def get(self):
        return await self.queue.get()

    def get_nowait(self):
        return self.queue.get_nowait()

    async def put(self, item):
        await self.queue.put(item)

    def put_nowait(self, item):
        self.queue.put_nowait(item)
    
    def task_done(self):
        self.queue.task_done()

    def empty(self):
        return self.queue.empty()
