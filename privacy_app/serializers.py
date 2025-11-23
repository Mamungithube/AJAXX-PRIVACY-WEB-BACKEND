from rest_framework import serializers
from .models import OpteryScanHistory

class OpteryScanHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OpteryScanHistory
        fields = "__all__"
