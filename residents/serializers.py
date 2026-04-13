'''
Serializers for REST Framework.
'''

# pylint: disable=trailing-whitespace
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'pcn',
            'uin',
            'issued_at',
            'active',
            'email',
            'phone_number',
            'registered_services'
        ]
