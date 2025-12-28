"""
Временное хранилище файлов.

Для production использовать Redis или S3.
"""

import time
from dataclasses import dataclass
from threading import Lock


@dataclass
class StoredFile:
    """Хранимый файл."""

    data: bytes
    filename: str
    content_type: str
    created_at: float
    ttl_seconds: int = 3600  # 1 час по умолчанию


class FileStorage:
    """
    In-memory хранилище файлов.

    Для локальной разработки и тестирования.
    В production заменить на Redis/S3.
    """

    def __init__(self):
        self._files: dict[str, StoredFile] = {}
        self._lock = Lock()

    def save(
        self,
        file_id: str,
        data: bytes,
        filename: str = "labels.pdf",
        content_type: str = "application/pdf",
        ttl_seconds: int = 3600,
    ) -> None:
        """Сохранить файл."""
        with self._lock:
            self._files[file_id] = StoredFile(
                data=data,
                filename=filename,
                content_type=content_type,
                created_at=time.time(),
                ttl_seconds=ttl_seconds,
            )

    def get(self, file_id: str) -> StoredFile | None:
        """Получить файл по ID."""
        with self._lock:
            stored = self._files.get(file_id)
            if stored is None:
                return None

            # Проверяем TTL
            if time.time() - stored.created_at > stored.ttl_seconds:
                del self._files[file_id]
                return None

            return stored

    def delete(self, file_id: str) -> bool:
        """Удалить файл."""
        with self._lock:
            if file_id in self._files:
                del self._files[file_id]
                return True
            return False

    def cleanup_expired(self) -> int:
        """Очистить просроченные файлы."""
        now = time.time()
        expired = []
        with self._lock:
            for file_id, stored in self._files.items():
                if now - stored.created_at > stored.ttl_seconds:
                    expired.append(file_id)
            for file_id in expired:
                del self._files[file_id]
        return len(expired)


# Глобальный экземпляр хранилища
file_storage = FileStorage()
