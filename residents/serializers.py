'''
Serializers for REST Framework.
'''

# pylint: disable=trailing-whitespace
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring


from django.contrib.auth.models import Group, User
from rest_framework import serializers

from .models import Resident, ResidentSector


class UserGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ["id", "name"]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username"]


class SectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResidentSector
        fields = "__all__"


class ResidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resident
        exclude = ["id", "proof_of_residence", "profile_image"]
