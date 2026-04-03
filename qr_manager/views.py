from rest_framework.decorators import api_view, authentication_classes, permission_classes

from .main import sign_message, verify_message, encrypt_message, decrypt_message


@api_view(['POST'])
def sign_message(request):
    pass


@api_view(['POST'])
def verify_message(request):
    pass


@api_view(['POST'])
def encrypt_message(request):
    pass


@api_view(['POST'])
def decrypt_message(request):
    pass