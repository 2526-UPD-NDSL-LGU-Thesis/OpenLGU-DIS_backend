'''
Generate a private key for signing QR data.
'''

from pathlib import Path
import os

from django.core.management.base import BaseCommand
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives import serialization


PRIVATE_SIGNING_KEY_PATH = Path(r"./qr_manager/private_signing_key.pem")
PRIVATE_ENCRYPTING_KEY_PATH = Path(r"./qr_manager/private_encrypting_key.pem")
PUBLIC_SIGNING_KEY_PATH = Path(r"./qr_manager/public_signing_key.pem")
PUBLIC_ENCRYPTING_KEY_PATH = Path(r"./qr_manager/public_encrypting_key.pem")
PRIVATE_KEY_PASSWORD = b"password"


# TODO: Implement flags
class Command(BaseCommand):             # pylint: disable=missing-class-docstring
    help = "Generate private keys for signing and encrypting QRs."

    def handle(
            self,
            *args,
            private_signing_key_path : Path = PRIVATE_SIGNING_KEY_PATH,
            private_encrypting_key_path : Path = PRIVATE_ENCRYPTING_KEY_PATH,
            public_signing_key_path : Path = PUBLIC_SIGNING_KEY_PATH,
            public_encrypting_key_path : Path = PUBLIC_ENCRYPTING_KEY_PATH,
            private_signing_key_password : bytes = PRIVATE_KEY_PASSWORD,
            private_encrypting_key_password : bytes = PRIVATE_KEY_PASSWORD,
            **options
        ) -> str | None:
        # Check if there exists a key in the system.
        # Raise a warning in the terminal before proceeding to generation.
        if any([
            os.path.isfile(private_signing_key_path),
            os.path.isfile(private_encrypting_key_path),
            os.path.isfile(public_signing_key_path),
            os.path.isfile(public_encrypting_key_path),
        ]):
            for _ in range(5):
                self.stderr.write(
                    self.style.WARNING(
                        "A key currently exists in system. Do you wish to proceed? (Y/N): "
                    ),
                    ending=""
                )
                confirm = input().strip().lower()
                if confirm in ("y", "yes", "n", "no"):
                    break

            if confirm != "y":
                self.stderr.write(
                    self.style.ERROR("Key generation cancelled by user.")
                )
                return

        try:
            signing_key = Ed25519PrivateKey.generate()

            private_signing_pem = signing_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.BestAvailableEncryption(private_signing_key_password)
            )

            with open(private_signing_key_path, "wb") as key:
                key.write(private_signing_pem)

            os.chmod(private_signing_key_path, 0o600)

            self.stdout.write(
                self.style.SUCCESS(f"Successfully generated a private signing key at {private_signing_key_path}.")
            )

            public_signing_pem = signing_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )

            with open(public_signing_key_path, "wb") as key:
                key.write(public_signing_pem)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully generated a public signing key at {public_signing_key_path}."
                )
            )
        except:                         # pylint: disable=bare-except
            self.stderr.write(
                self.style.ERROR("Failed to generate signing keys.")
            )

        try:
            encrypting_key = X25519PrivateKey.generate()

            private_encrypting_pem = encrypting_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.BestAvailableEncryption(private_encrypting_key_password)
            )

            with open(private_encrypting_key_path, "wb") as key:
                key.write(private_encrypting_pem)

            os.chmod(private_encrypting_key_path, 0o600)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully generated a private encrypting key at {private_encrypting_key_path}."
                )
            )

            public_encrypting_pem = encrypting_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )

            with open(public_encrypting_key_path, "wb") as key:
                key.write(public_encrypting_pem)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully generated a public encrypting key at {public_encrypting_key_path}."
                )
            )
        except:                         # pylint: disable=bare-except
            self.stderr.write(
                self.style.ERROR("Failed to generate encrypting keys.")
            )
