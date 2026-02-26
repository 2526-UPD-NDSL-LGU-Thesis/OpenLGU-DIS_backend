from pathlib import Path
from typing import Optional

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes


# TODO: use .env
PRIVATE_KEY_PATH = Path(r"./qr_manager/private_key.pem")
PRIVATE_KEY_PASSWORD = b"password"


def _load_key(               # pylint: disable=missing-function-docstring
    key_path : Path,
    password : Optional[bytes] = None
) -> PrivateKeyTypes :
    if not key_path.exists():
        raise FileNotFoundError(f"Private key not found at {key_path}")
    
    with open("./qr_manager/private_key.pem", "rb") as key:
        return serialization.load_pem_private_key(
            key.read(),
            password=password
        )


def generate_qr():
    private_key = _load_key(PRIVATE_KEY_PATH, PRIVATE_KEY_PASSWORD)
    pass


def authenticate_qr():
    private_key = _load_key(PRIVATE_KEY_PATH, PRIVATE_KEY_PASSWORD)
    pass
