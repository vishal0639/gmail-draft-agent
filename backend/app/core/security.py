"""Token and preference encryption at rest (Fernet)."""

import json
import logging
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings

_log = logging.getLogger(__name__)


def _fernet() -> Fernet:
    s = get_settings()
    key = (s.master_encryption_key or "").strip()
    if not key:
        raise RuntimeError(
            "MASTER_ENCRYPTION_KEY is not set. Generate: "
            'python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
        )
    return Fernet(key.encode("utf-8"))


def encrypt_str(plain: str) -> str:
    return _fernet().encrypt(plain.encode("utf-8")).decode("utf-8")


def decrypt_str(token: str) -> str:
    try:
        return _fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        _log.warning("Decryption failed (wrong key or corrupted data)")
        raise


def encrypt_json(data: dict[str, Any]) -> str:
    return encrypt_str(json.dumps(data, ensure_ascii=False))


def decrypt_json(blob: str) -> dict[str, Any]:
    return json.loads(decrypt_str(blob))
