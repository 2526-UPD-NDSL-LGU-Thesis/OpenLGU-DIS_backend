'''
Generate a private key for signing QR data.
'''

from pathlib import Path
import os

from django.core.management.base import BaseCommand
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

PRIVATE_KEY_PATH = Path(r"./qr_manager/private_key.pem")
PRIVATE_KEY_PASSWORD = b"password"


class Command(BaseCommand):             # pylint: disable=missing-class-docstring
    help = "Generate an EdDSA key for data encryption and signing"

    def handle(self, *args, **options) -> str | None:
        try:
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

            self.stdout.write(
                self.style.SUCCESS(f"Generated encryption key at {PRIVATE_KEY_PATH}.")
            )
        except:                         # pylint: disable=bare-except
            self.stderr.write(
                self.style.ERROR("Failed to generate encrpytion key.")
            )

