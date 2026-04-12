"""
ID generator for services.
"""

import secrets
import string


def generate_id(length : int = 10) -> str :
    """Cryptographically generate a random UID."""
    return ''.join(secrets.choice(string.digits) for _ in range(length))
