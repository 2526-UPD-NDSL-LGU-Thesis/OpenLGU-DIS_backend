from django.test import TestCase

from .main import pycose_sign_message, pycose_verify_message

# Create your tests here.

payload = b"hello"

test = pycose_sign_message(payload)
