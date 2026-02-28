'''
Generate a private key for signing QR data.
'''

from pathlib import Path
import os

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

PRIVATE_KEY_PATH = Path(r"./qr_manager/private_key.pem")
PRIVATE_KEY_PASSWORD = b"password"


def main():         # pylint: disable=missing-function-docstring
    private_key = Ed25519PrivateKey.generate()

    password = PRIVATE_KEY_PASSWORD     # TODO: Use .env

    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.BestAvailableEncryption(password)
    )

    with open(PRIVATE_KEY_PATH, "wb") as key:
        key.write(pem)

    os.chmod(PRIVATE_KEY_PATH, 0o600)

if __name__ == "__main__":
    main()
