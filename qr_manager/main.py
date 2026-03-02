'''

'''

from pathlib import Path
from typing import Optional, Dict, Tuple, Any

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

# TODO: use .env
PRIVATE_KEY_PATH = Path(r"./qr_manager/private_key.pem")
PRIVATE_KEY_PASSWORD = b"password"


def _load_private_key(                      # pylint: disable=missing-function-docstring
    key_path : Path,
    password : Optional[bytes] = None
) -> PrivateKeyTypes :
    if not key_path.exists():
        raise FileNotFoundError(f"Private key not found at {key_path}")
    
    with open(key_path, "rb") as key:
        return serialization.load_pem_private_key(
            key.read(),
            password=password
        )


def _load_cose_key() -> CoseKey:            # pylint: disable=missing-function-docstring
    private_key = _load_private_key(PRIVATE_KEY_PATH, PRIVATE_KEY_PASSWORD)
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


def generate(message : Dict[str, Any]) -> bytes :
    """Generate a signed COSE_Sign1 from given message."""
    cose_key = _load_cose_key()
    
    payload = cbor2.dumps(message)

    sign1_message = Sign1Message(
        phdr={Algorithm: EdDSA},
        payload=payload
    )
    sign1_message.key = cose_key

    return sign1_message.encode()


def authenticate(message : str | bytes) -> Tuple[bool, Dict[str, Any]] :
    """Verify signed message"""
    cose_key = _load_cose_key()
    
    try:
        decoded = Sign1Message.decode(message)    
        decoded.key = cose_key

        algorithm = decoded.phdr.get(Algorithm)

        if algorithm != EdDSA:
            return False, { "error" : f"Cannot verify message encrypted in {algorithm}" }

        # Add payload checking

        payload = cbor2.loads(decoded.payload)

        return decoded.verify_signature(), payload or None
    except:
        return False, None