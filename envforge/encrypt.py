"""Optional encryption support for snapshot values using Fernet symmetric encryption."""

import base64
import os
from typing import Dict

try:
    from cryptography.fernet import Fernet, InvalidToken
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


ENVFORGE_KEY_ENV = "ENVFORGE_ENCRYPTION_KEY"


def _require_crypto() -> None:
    if not CRYPTO_AVAILABLE:
        raise RuntimeError(
            "cryptography package is required for encryption support. "
            "Install it with: pip install cryptography"
        )


def generate_key() -> str:
    """Generate a new Fernet key and return it as a base64 string."""
    _require_crypto()
    return Fernet.generate_key().decode()


def get_key_from_env() -> str:
    """Read the encryption key from the ENVFORGE_ENCRYPTION_KEY environment variable."""
    key = os.environ.get(ENVFORGE_KEY_ENV)
    if not key:
        raise RuntimeError(
            f"Encryption key not found. Set the {ENVFORGE_KEY_ENV} environment variable."
        )
    return key


def encrypt_values(values: Dict[str, str], key: str) -> Dict[str, str]:
    """Encrypt all values in a dict using the provided Fernet key."""
    _require_crypto()
    f = Fernet(key.encode() if isinstance(key, str) else key)
    return {
        k: "enc:" + f.encrypt(v.encode()).decode()
        for k, v in values.items()
    }


def decrypt_values(values: Dict[str, str], key: str) -> Dict[str, str]:
    """Decrypt all values in a dict that are prefixed with 'enc:'."""
    _require_crypto()
    f = Fernet(key.encode() if isinstance(key, str) else key)
    result = {}
    for k, v in values.items():
        if v.startswith("enc:"):
            try:
                result[k] = f.decrypt(v[4:].encode()).decode()
            except InvalidToken as e:
                raise ValueError(f"Failed to decrypt value for key '{k}': invalid token") from e
        else:
            result[k] = v
    return result


def is_encrypted(values: Dict[str, str]) -> bool:
    """Return True if any value in the dict appears to be encrypted."""
    return any(v.startswith("enc:") for v in values.values())
