'''
Module for creating COSE_Sign1 signed messages using EdDSA Algorithm for QR generation.

To start signing messages, first generate the key through the python script:
```python
python ./scripts/generate_key.py
```

Generate messages with `sign_eddsa` and verify messages with `verify_eddsa`.
'''

from .main import (
    pycose_sign_message, pycose_verify_message
)

from .utils import (
    read_qr, read_qr_image
)
