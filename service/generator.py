"""
ID generator for services.
"""

import secrets
import string


def generate_id(length : int = 10) -> str :
    """Cryptographically generate a random UID."""
    while True:
        _id = ''.join(secrets.choice(string.digits) for _ in range(length))

        if _id[0] != "0" and len(_id) == length: 
            return _id
