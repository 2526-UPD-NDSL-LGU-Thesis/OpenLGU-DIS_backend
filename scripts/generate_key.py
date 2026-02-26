'''
Generate a private key for signing QR data.
'''


from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

def main():         # pylint: disable=missing-function-docstring
    private_key = Ed25519PrivateKey.generate()

    password = b"password"      # TODO: Use .env

    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.BestAvailableEncryption(password)
    )

    with open(r"./qr_manager/private_key.pem", "wb") as key:
        key.write(pem)

if __name__ == "__main__":
    main()
