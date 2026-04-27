# pylint: disable=missing-module-docstring
# pylint: disable=trailing-whitespace

from pathlib import Path
from typing import Optional, Dict, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import zlib

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes
from pycose.messages.sign1message import Sign1Message
from pycose.keys.cosekey import CoseKey
from pycose.headers import Algorithm
from pycose.algorithms import EdDSA
from pycose.keys.curves import Ed25519
from pycose.keys.keyparam import KpKty, OKPKpD, OKPKpX, KpAlg, KpKeyOps, OKPKpCurve
from pycose.keys.keytype import KtyOKP
from pycose.keys.keyops import SignOp, VerifyOp
import cbor2

from cryptography.hazmat.primitives.serialization import (load_pem_private_key, load_pem_public_key)
from nacl.exceptions import BadSignatureError
from nacl.public import PrivateKey, PublicKey, Box
from nacl.signing import SigningKey, VerifyKey, SignedMessage
from pydantic import ValidationError
import base45
import cbor2

# from .claim169 import CBORWebToken

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


def pycose_sign_message(payload : bytes) -> bytes :
    """Generate a COSE_Sign1 signed message with EdDSA Algorithm with the base cryptography library.

    :param message: Message to be encrypted and signed.
    :type message: Dict[str, Any]
    :return: COSE_Sign1 signed message.
    :rtype: bytes
    """
    with open(PRIVATE_SIGNING_KEY_PATH, "rb") as key:
        # private_key = load_pem_private_key(
        #     key.read(),
        #     PRIVATE_KEY_PASSWORD
        # )

        private_key = CoseKey.from_pem_private_key(
            key.read(),
            password=PRIVATE_KEY_PASSWORD
        )

    sign1_message = Sign1Message(
        phdr={ Algorithm: EdDSA },
        payload=payload
    )
    sign1_message.key = private_key

    return sign1_message.encode()           #type: ignore


def pynacl_sign_message(
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


def pycose_verify_message(message : bytes) -> Tuple[bool, Dict[str, Any]] :
    """Verify COSE_Sign1 signed message with COSE key with EdDSA Algorithm with the base cryptography library.

    :param message: Encrypted message to be verified.
    :type message: bytes
    :return: Returns authentication status and the encrypted message's payload.
    :rtype: Tuple[bool, Dict[str, Any]]
    """
    with open(PRIVATE_SIGNING_KEY_PATH, "rb") as key:
        private_key = load_pem_private_key(
            key.read(),
            PRIVATE_KEY_PASSWORD
        )
    
    try:
        decoded = Sign1Message.decode(message)
        decoded.key = private_key

        algorithm = decoded.phdr.get(Algorithm)

        if algorithm != EdDSA:
            return False, { "error" : f"Cannot verify message encrypted in {algorithm}" }

        if decoded.payload is None:
            return False, { "error" : "Payload is empty" }
        payload = cbor2.loads(decoded.payload)

        try:
            QRInfo(**payload)
        except TypeError:
            return False, { "error" : "Payload is missing information/s" }

        return decoded.verify_signature(), payload or {} #type: ignore
    except:                                 # pylint: disable=bare-except
        return False, { "error" : "Failed to decode message" }


def pynacl_verify_message(
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
    try:
        b45_qr = base45.b45decode(qr_code)
    except:
        return False, { "error" : "error_not_base45" }

    try:
        decompressed_qr = zlib.decompress(b45_qr)
    except:
        return False, { "error" : "error_not_compressed" }

    # try:
    #     decrypt_msg = decrypt_message(decompressed_qr)
    # except Exception:
    #     pass

    try:
        signed_msg = pynacl_verify_message(decompressed_qr)
    except BadSignatureError:
        return False, { "error" : "error_tampered" }
    
    try:
        # cwt = CBORWebToken.from_cbor(signed_msg)
        cwt = cbor2.loads(signed_msg)
        cwt[169] = cbor2.loads(cwt[169])

        return True, cwt
    except ValidationError as err:
        return False, { "error" : "error_other", "errors" : err }
