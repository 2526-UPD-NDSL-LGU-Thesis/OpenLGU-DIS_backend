'''
Serializers for REST Framework.
'''

__all__ = (
    'CompSciLabs',
    'CompSciDeptIDSerializer',
    'CompSciLabIDSerializer',
)

from rest_framework import serializers

from .models import CompSciLabID, CompSciDeptID, CompSciLabs


class CompSciLabsSerializer(serializers.ModelSerializer):
    '''Serializer for CompSciLabs.'''
    class Meta:
        '''Meta class for CompSciLabs Serializer.'''
        model = CompSciLabs
        fields = '__all__'


class CompSciDeptIDSerializer(serializers.ModelSerializer):
    '''Serializer for CompSciDeptID.'''
    class Meta:
        '''Meta class for CompSciDeptID Serializer.'''
        model = CompSciDeptID
        fields = '__all__'


class CompSciLabIDSerializer(serializers.ModelSerializer):
    '''Serializer for CompSciLabID.'''
    class Meta:
        '''Meta class for CompSciLabID Serializer.'''
        model = CompSciLabID
        fields = '__all__'
