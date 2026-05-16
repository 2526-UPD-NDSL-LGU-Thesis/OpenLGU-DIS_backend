from rest_framework import serializers
from django.contrib.auth.models import User

from residents.models import Resident
from .models import Service, Claim, Group, Assignment


class ServiceSerializer(serializers.ModelSerializer):
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


class ClaimSerializer(serializers.ModelSerializer):
    user = ClaimUserSerializer(read_only=True)
    claimed_by = ClaimOfficialSerializer(read_only=True)

    class Meta:
        model = Claim
        exclude = ["id"]


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        exclude = ["id"]


class AssignmentSerializer(serializers.ModelSerializer):
    groups = GroupSerializer(many=True, read_only=True)

    class Meta:
        model = Assignment
        exclude = ["id"]
