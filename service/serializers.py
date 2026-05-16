from rest_framework import serializers
from .models import Service, Claim, Group, Assignment


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = "__all__"


class ClaimSerializer(serializers.ModelSerializer):
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
