"""
Serializers for Service models.
"""

# pylint: disable=trailing-whitespace
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring


from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.models import Group as BaseGroup

from residents.models import Resident, Sector
from .models import Service, Claim, Group, Assignment


class ServiceSectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sector
        fields = ["name"]


class ServiceGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseGroup
        fields = ["name"]


class ServiceSerializer(serializers.ModelSerializer):
    recipient_sectors = ServiceSectorSerializer(many=True, read_only=True)
    allowed_groups = ServiceGroupSerializer(many=True, read_only=True)
    
    class Meta:
        model = Service
        fields = "__all__"


class ClaimUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resident
        fields = ["uin", "pcn"]


class ClaimOfficialSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name"]


class ClaimServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ["id", "name", "description"]


class ClaimSerializer(serializers.ModelSerializer):
    user = ClaimUserSerializer(read_only=True)
    claimed_by = ClaimOfficialSerializer(read_only=True)
    service = ClaimServiceSerializer(read_only=True)

    class Meta:
        model = Claim
        exclude = ["id"]


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = "__all__"


class AssignmentGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        exclude = ["id"]


class AssignmentSerializer(serializers.ModelSerializer):
    groups = AssignmentGroupSerializer(many=True, read_only=True)

    class Meta:
        model = Assignment
        exclude = ["id"]
