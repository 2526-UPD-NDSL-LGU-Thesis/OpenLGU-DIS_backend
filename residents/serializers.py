'''
Serializers for REST Framework.
'''

# pylint: disable=trailing-whitespace
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring


from django.contrib.auth.models import Group as BaseGroup
from django.contrib.auth.models import User
from rest_framework import serializers

from service.models import Group
from service.serializers import AssignmentSerializer
from .models import Resident, Sector


class UserGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseGroup
        fields = ["name"]


class UserClaimingGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ["name"]

class UserSerializer(serializers.ModelSerializer):
    groups = UserGroupSerializer(many=True, read_only=True)
    assignment = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "groups", "assignment", "is_superuser"]

    def get_assignment(self, obj):
        if hasattr(obj, "official"):
            return AssignmentSerializer(obj.official).data
        return None


class SectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sector
        fields = "__all__"


class ResidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resident
        exclude = ["id", "proof_of_residence", "profile_image"]
