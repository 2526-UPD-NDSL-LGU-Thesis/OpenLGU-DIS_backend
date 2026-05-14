from rest_framework import serializers
from .models import Service, Claim


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = "__all__"


class ServiceClaimSerializer(serializers.ModelSerializer):
    class Meta:
        model = Claim
        exclude = ["id"]
