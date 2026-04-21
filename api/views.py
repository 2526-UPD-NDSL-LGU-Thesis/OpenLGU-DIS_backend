'''
Django views for API.
'''

from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get("username")
    password = request.data.get("password")

    user = authenticate(request, username=username, password=password)

    if user is not None:
        login(request, user)  # 🔥 creates session
        return Response({"message": "Logged in"})
    else:
        return Response({"error": "Invalid credentials"}, status=400)
#TODO: add 'credentials: "include"' to HTTP Requests


@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def ping(_) -> Response :
    return Response({ "message" : "pong" }, status=200)

@api_view(['GET'])
def user_ping(_) -> Response :
    return Response({ "message" : "pong"}, status=200)

@ensure_csrf_cookie
def get_csrf(_) -> Response :
    return Response({ "detail" : "CSRF cookie set" }, status=200)
