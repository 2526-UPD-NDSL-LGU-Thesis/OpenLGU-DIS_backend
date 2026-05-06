# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=trailing-whitespace


from typing import Dict
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import (
    load_pem_private_key, load_pem_public_key
)
from pycose.messages.sign1message import Sign1Message
from pycose.keys.cosekey import CoseKey
from pycose.headers import Algorithm
from pycose.algorithms import EdDSA
from pycose.keys.curves import Ed25519
from pycose.keys.keyparam import KpKty, OKPKpD, OKPKpX, KpAlg, KpKeyOps, OKPKpCurve
from pycose.keys.keytype import KtyOKP
from pycose.keys.keyops import SignOp, VerifyOp
import cbor2


# TODO: use .env
PRIVATE_SIGNING_KEY_PATH = Path(r"./qr_manager/private_signing_key.pem")
PRIVATE_ENCRYPTING_KEY_PATH = Path(r"./qr_manager/private_encrypting_key.pem")
PUBLIC_SIGNING_KEY_PATH = Path(r"./qr_manager/public_signing_key.pem")
PUBLIC_ENCRYPTING_KEY_PATH = Path(r"./qr_manager/public_encrypting_key.pem")

PRIVATE_KEY_PASSWORD = b"password"


def _load_private_signing_key(path_to_key : Path, password : bytes) -> CoseKey :
    with open(path_to_key, "rb") as key:
        private_key = load_pem_private_key(
            key.read(),
            password
        )

    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    public_key = private_key.public_key()
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    
    cose_key = {
        KpKty: KtyOKP,
        KpAlg: EdDSA,
        OKPKpCurve: Ed25519,
        KpKeyOps: [SignOp, VerifyOp],
        OKPKpD: private_bytes,
        OKPKpX: public_bytes
    }

    return CoseKey.from_dict(cose_key)


def _load_public_signing_key(path_to_key : Path) -> CoseKey :
    with open(path_to_key, "rb") as key:
        public_key = load_pem_public_key(
            key.read(),
        )
    
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )

    cose_key = {
        KpKty: KtyOKP,
        KpAlg: EdDSA,
        OKPKpCurve: Ed25519,
        OKPKpX: public_bytes
    }

    return CoseKey.from_dict(cose_key)


def pycose_sign_message(payload : bytes) -> bytes :
    """Generate a COSE_Sign1 message with EdDSA Algorithm using the base cryptography library.

    _extended_summary_

    Args:
        payload (bytes): CBOR payload to be signed.

    Returns:
        bytes:  A COSE_Sign1 message bytes.
    """
    if not isinstance(payload, (bytes, bytearray)):
        raise TypeError("Payload must be of type bytes or bytearray.")

    try:
        cbor2.loads(payload)
    except Exception as err:
        raise ValueError("Payload is not a valid CBOR object.") from err

    try:
        cose_key = _load_private_signing_key(PRIVATE_SIGNING_KEY_PATH, PRIVATE_KEY_PASSWORD)
    except Exception as err:
        raise ValueError("Failed to load private signing key.") from err

    sign1_message = Sign1Message(
        phdr={ Algorithm: EdDSA },
        payload=payload
    )
    sign1_message.key = cose_key

    return sign1_message.encode()           #type: ignore


def pycose_verify_message(message : bytes) -> Dict :
    """Verifies signature of a signed message with the public key.

    Args:
        message (bytes): Bytes message to be verified.

    Returns:
        Dict: Returns the payload of the COSE_Sign1 message.
    """
    if not isinstance(message, (bytes, bytearray)):
        raise TypeError("Payload must be of type bytes or bytearray.")
    
    try:
        signed_message = Sign1Message.decode(message)
    except Exception as err:
        raise TypeError("Message is not a valid Sign1Message.") from err
    
    try:
        cose_key = _load_public_signing_key(PUBLIC_SIGNING_KEY_PATH)
        signed_message.key = cose_key
    except Exception as err:
        raise ValueError("Failed to load public signing key.") from err
    
    algorithm = signed_message.phdr.get(Algorithm)

    if algorithm != EdDSA:
        raise ValueError(f"Invalid algorithm. Expected EdDSA, got {algorithm} instead.")

    if signed_message.payload is None:
        raise ValueError(f"Payload is empty.")
    
    valid = signed_message.verify_signature()
    if not valid:
        raise ValueError("Invalid signature. Message may be tampered or key used was invalid.")
    
    try:
        payload = cbor2.loads(signed_message.payload)
    except Exception as err:
        raise TypeError("Payload is not a valid CBOR object.")
    
    #TODO: Check Content

    return payload
