'''
Serializers for REST Framework.
'''

__all__ = (
    'UserSerializer',
)

from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    '''Serializer for User.'''
    class Meta:
        '''Meta class for User Serializer.'''
        model = User
        fields = '__all__'