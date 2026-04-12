# pylint: disable=missing-module-docstring
# pylint: disable=trailing-whitespace

from pathlib import Path
from typing import Dict, Tuple
from dataclasses import dataclass
from datetime import datetime
import zlib

import base45
from cryptography.hazmat.primitives.serialization import (load_pem_private_key, load_pem_public_key)
from nacl.exceptions import BadSignatureError
from nacl.public import PrivateKey, PublicKey, Box
from nacl.signing import SigningKey, VerifyKey, SignedMessage
from pydantic import ValidationError

from .claim169 import CBORWebToken

# TODO: use .env
PRIVATE_SIGNING_KEY_PATH = Path(r"./qr_manager/private_signing_key.pem")
PRIVATE_ENCRYPTING_KEY_PATH = Path(r"./qr_manager/private_encrypting_key.pem")
PUBLIC_SIGNING_KEY_PATH = Path(r"./qr_manager/public_signing_key.pem")
PUBLIC_ENCRYPTING_KEY_PATH = Path(r"./qr_manager/public_encrypting_key.pem")

PRIVATE_KEY_PASSWORD = b"password"

@dataclass
class QRInfo:
    """Class for checking proper headers with payload.
    """
    id : str
    pcn  : int
    issued_at : datetime
    verified : bool
    email : str
    phone_number : str
    face_data : bytes


def _load_signing_key(
        path_to_key : Path = PRIVATE_SIGNING_KEY_PATH,
        password : bytes = PRIVATE_KEY_PASSWORD
    ) :          # pylint: disable=missing-function-docstring
    with open(path_to_key, "rb") as key:
        signing_key = load_pem_private_key(
            key.read(),
            password=password
        )
    
    return SigningKey(signing_key.private_bytes_raw())


def _load_verify_key(
        path_to_key : Path = PUBLIC_SIGNING_KEY_PATH,
    ) :          # pylint: disable=missing-function-docstring
    with open(path_to_key, "rb") as key:
        verify_key = load_pem_public_key(
            key.read()
        )
    
    return VerifyKey(verify_key.public_bytes_raw())


def _load_encrypting_key(
        path_to_key : Path = PRIVATE_ENCRYPTING_KEY_PATH,
        password : bytes = PRIVATE_KEY_PASSWORD
    ) :
    with open(path_to_key, "rb") as key:
        encrypting_key = load_pem_private_key(
            key.read(),
            password=password
        )
    
    return PrivateKey(encrypting_key.private_bytes_raw())


def _load_decrypting_key(
        path_to_key : Path = PUBLIC_ENCRYPTING_KEY_PATH,
    ) :          # pylint: disable=missing-function-docstring
    with open(path_to_key, "rb") as key:
        verify_key = load_pem_public_key(
            key.read()
        )
    
    return PublicKey(verify_key.public_bytes_raw())


def _load_cipher_box(
        path_to_private_key : Path = PRIVATE_ENCRYPTING_KEY_PATH,
        path_to_public_key : Path = PUBLIC_ENCRYPTING_KEY_PATH,
        password : bytes = PRIVATE_KEY_PASSWORD
    ):
    private_key = _load_encrypting_key(path_to_private_key, password)
    public_key = _load_decrypting_key(path_to_public_key)

    return Box(private_key, public_key)

def sign_message(
        message : bytes,
        path_to_key : Path = PRIVATE_SIGNING_KEY_PATH,
        password : bytes = PRIVATE_KEY_PASSWORD
    ) -> SignedMessage :
    """Generate a COSE_Sign1 signed message with EdDSA Algorithm.

    :param message: Message in bytes to be verified.
    :type message: bytes
    :return: Returns a `nacl.signing.SignedMessage`.
    :rtype: SignedMessage
    """
    signing_key = _load_signing_key(path_to_key, password)

    return signing_key.sign(message)


def verify_message(
        signed_message : bytes,
        path_to_key : Path = PUBLIC_SIGNING_KEY_PATH,
    ) -> bytes :
    """Verify COSE_Sign1 signed message with COSE key with EdDSA Algorithm.

    :param message: Encrypted message to be verified.
    :type message: bytes
    :return: Returns authentication status and the encrypted message's payload.
    :rtype: Tuple[bool, Dict[str, Any]]
    """
    verify_key = _load_verify_key(path_to_key)
    
    return verify_key.verify(signed_message)


def encrypt_message(
        message,
        path_to_private_key : Path = PRIVATE_ENCRYPTING_KEY_PATH,
        path_to_public_key : Path = PUBLIC_ENCRYPTING_KEY_PATH,
        password : bytes = PRIVATE_KEY_PASSWORD
    ):
    """Encrypt message with XSalsa20-Poly1305 using Diffie-Hellman key exchange.

    Args:
        message (_type_): _description_
        path_to_private_key (Path, optional): _description_. Defaults to PRIVATE_ENCRYPTING_KEY_PATH.
        path_to_public_key (Path, optional): _description_. Defaults to PUBLIC_ENCRYPTING_KEY_PATH.
        password (bytes, optional): _description_. Defaults to PRIVATE_KEY_PASSWORD.

    Returns:
        _type_: _description_
    """
    box = _load_cipher_box(path_to_private_key, path_to_public_key, password)

    return box.encrypt(message)


def decrypt_message(
        message,
        path_to_private_key : Path = PRIVATE_ENCRYPTING_KEY_PATH,
        path_to_public_key : Path = PUBLIC_ENCRYPTING_KEY_PATH,
        password : bytes = PRIVATE_KEY_PASSWORD
    ):
    box = _load_cipher_box(path_to_private_key, path_to_public_key, password)

    return box.decrypt(message)


def validate_qr(qr_code : str) -> Tuple[bool, Dict] :
    """Validates QR code. Returns the payload, if successful. Else, returns an error message.

    Args:
        qr_code (str): QR code in base45 string.

    Returns:
        Tuple[bool, Dict]: Status of validation and the payload.
    """
    b45_qr = base45.b45decode(qr_code)

    decompressed_qr = zlib.decompress(b45_qr)

    # try:
    #     decrypt_msg = decrypt_message(decompressed_qr)
    # except Exception:
    #     pass

    try:
        signed_msg = verify_message(decompressed_qr)
    except BadSignatureError:
        return False, { "error" : "Failed to verify QR" }
    
    try:
        cwt = CBORWebToken.from_cbor(signed_msg)

        return True, cwt.model_dump()
    except ValidationError as err:
        return False, { "error" : "Failed to parse QR payload", "errors" : err }
