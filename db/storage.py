"""Storage factory and convenience exports."""
from utils.config import get_settings

from db.backends.base import StorageBackend

from db.backends.supabase_backend import SupabaseStorageBackend
from db.backends.file_backend import FileStorageBackend



def get_storage_backend() -> StorageBackend:
    """
    Factory that returns the configured StorageBackend (Supabase or file).
    Handles backend selection, error handling, and connection management.
    """
    settings = get_settings()
    backend = (settings.storage_backend or "file").lower()

    if backend == "supabase":
        try:
            return SupabaseStorageBackend()
        except Exception as exc:
            from utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Failed to initialize Supabase backend: {exc}")
            raise RuntimeError("Supabase backend initialization failed. Check credentials and connectivity.") from exc

    if backend == "file":
        raise NotImplementedError("FileStorageBackend is not implemented in this branch. Use 'supabase' for STORAGE_BACKEND.")

    raise RuntimeError(f"Unsupported storage backend: {backend}")


__all__ = [
    "StorageBackend",
    "get_storage_backend",
    "SupabaseStorageBackend",
    "FileStorageBackend",
]
