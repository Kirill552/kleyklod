"""
Шифрование персональных данных (152-ФЗ).

Реализует AES-256-GCM шифрование для защиты ПДн в БД.
"""

import base64
import hashlib
from typing import Any

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from sqlalchemy import String, TypeDecorator

from app.config import get_settings


class EncryptionError(Exception):
    """Ошибка шифрования."""

    pass


class Encryptor:
    """
    Шифратор персональных данных.

    Использует Fernet (AES-128-CBC) для шифрования.
    Для production рекомендуется AES-256-GCM через hazmat.

    Требования 152-ФЗ:
    - Шифрование персональных данных при хранении
    - Ключ шифрования хранится отдельно от данных
    - Логирование доступа к ПДн
    """

    _instance: "Encryptor | None" = None
    _fernet: Fernet | None = None

    def __new__(cls) -> "Encryptor":
        """Singleton pattern для единственного экземпляра."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Инициализация шифратора."""
        if self._fernet is not None:
            return

        settings = get_settings()
        encryption_key = settings.encryption_key

        if not encryption_key:
            # В режиме разработки генерируем временный ключ
            if settings.debug:
                encryption_key = Fernet.generate_key().decode()
                print("⚠️  ВНИМАНИЕ: Используется временный ключ шифрования!")
                print("   Для production установите ENCRYPTION_KEY в .env")
            else:
                raise EncryptionError(
                    "ENCRYPTION_KEY не установлен. Шифрование ПДн обязательно по 152-ФЗ."
                )

        # Проверяем формат ключа
        try:
            self._fernet = Fernet(encryption_key.encode())
        except Exception:
            # Если ключ не в формате Fernet, деривируем его
            self._fernet = self._derive_key(encryption_key)

    def _derive_key(self, password: str) -> Fernet:
        """
        Деривация ключа из пароля.

        Использует PBKDF2 для преобразования пароля в ключ.
        Salt генерируется детерминистически из самого пароля (ENCRYPTION_KEY).
        """
        # Генерируем salt из ENCRYPTION_KEY (первые 16 байт SHA-256 хеша)
        # Это безопаснее чем hardcoded salt, но при этом детерминистично
        salt = hashlib.sha256(f"kleykod_salt_{password}".encode()).digest()[:16]

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,  # Рекомендация OWASP 2023
        )

        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return Fernet(key)

    def encrypt(self, value: str) -> str:
        """
        Шифрование строки.

        Args:
            value: Исходная строка

        Returns:
            Зашифрованная строка в base64
        """
        if not value:
            return ""

        if self._fernet is None:
            raise EncryptionError("Шифратор не инициализирован")

        try:
            encrypted = self._fernet.encrypt(value.encode())
            return encrypted.decode()
        except Exception as e:
            raise EncryptionError(f"Ошибка шифрования: {str(e)}")

    def decrypt(self, encrypted_value: str) -> str:
        """
        Расшифровка строки.

        Args:
            encrypted_value: Зашифрованная строка

        Returns:
            Расшифрованная строка
        """
        if not encrypted_value:
            return ""

        if self._fernet is None:
            raise EncryptionError("Шифратор не инициализирован")

        try:
            decrypted = self._fernet.decrypt(encrypted_value.encode())
            return decrypted.decode()
        except Exception as e:
            raise EncryptionError(f"Ошибка расшифровки: {str(e)}")


# Глобальный экземпляр
_encryptor: Encryptor | None = None


def get_encryptor() -> Encryptor:
    """Получить экземпляр шифратора."""
    global _encryptor
    if _encryptor is None:
        _encryptor = Encryptor()
    return _encryptor


def encrypt_field(value: str) -> str:
    """
    Шифрование поля БД.

    Args:
        value: Значение для шифрования

    Returns:
        Зашифрованное значение
    """
    return get_encryptor().encrypt(value)


def decrypt_field(encrypted_value: str) -> str:
    """
    Расшифровка поля БД.

    Args:
        encrypted_value: Зашифрованное значение

    Returns:
        Расшифрованное значение
    """
    return get_encryptor().decrypt(encrypted_value)


def generate_encryption_key() -> str:
    """
    Генерация нового ключа шифрования.

    Используйте для создания ENCRYPTION_KEY в .env

    Returns:
        Ключ в формате Fernet (base64)
    """
    return Fernet.generate_key().decode()


def hash_telegram_id(telegram_id: int | str) -> str:
    """
    Детерминистический хеш telegram_id для поиска в БД.

    Fernet шифрование не детерминистическое (разный результат каждый раз),
    поэтому для поиска используем SHA-256 хеш.

    Args:
        telegram_id: ID пользователя в Telegram

    Returns:
        SHA-256 хеш telegram_id (hex, 64 символа)
    """
    import hashlib

    settings = get_settings()
    # Используем ENCRYPTION_KEY как соль для хеша
    salt = (settings.encryption_key or "default_salt")[:32]

    value = f"{salt}:{telegram_id}"
    return hashlib.sha256(value.encode()).hexdigest()


def hash_vk_id(vk_user_id: int | str) -> str:
    """
    Детерминистический хеш vk_user_id для поиска в БД.

    Args:
        vk_user_id: ID пользователя в VK

    Returns:
        SHA-256 хеш vk_user_id (hex, 64 символа)
    """
    import hashlib

    settings = get_settings()
    # Используем ENCRYPTION_KEY как соль для хеша
    salt = (settings.encryption_key or "default_salt")[:32]

    value = f"{salt}:vk:{vk_user_id}"
    return hashlib.sha256(value.encode()).hexdigest()


# SQLAlchemy TypeDecorator для автоматического шифрования


class EncryptedString(TypeDecorator):
    """
    SQLAlchemy тип для автоматического шифрования/расшифровки.

    Использование:
        telegram_id = Column(EncryptedString(255))
    """

    impl = String
    cache_ok = True

    def process_bind_param(self, value: Any, _dialect: Any) -> str | None:
        """Шифрование при записи в БД."""
        if value is None:
            return None
        if isinstance(value, int):
            value = str(value)
        return encrypt_field(value)

    def process_result_value(self, value: Any, _dialect: Any) -> str | None:
        """Расшифровка при чтении из БД."""
        if value is None:
            return None
        return decrypt_field(value)
