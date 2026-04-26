'''
Module for creating COSE_Sign1 signed messages using EdDSA Algorithm for QR generation.

To start signing messages, first generate the key through the python script:
```python
python ./scripts/generate_key.py
```

Generate messages with `sign_eddsa` and verify messages with `verify_eddsa`.
'''

from .main import (
    pynacl_sign_message, pynacl_verify_message, encrypt_message, decrypt_message, validate_qr
)

from .utils import (
    read_qr
)
