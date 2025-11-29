from rest_framework import serializers
from .models import OpteryScanHistory,OpteryMember

class OpteryScanHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OpteryScanHistory
        fields = "__all__"


class OpteryMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpteryMember
        fields = [
            'uuid', 'email', 'first_name', 'last_name', 'middle_name',
            'city', 'country', 'state', 'birthday_day', 'birthday_month',
            'birthday_year', 'plan', 'postpone_scan', 'group_tag',
            'address_line1', 'address_line2', 'zipcode', 'optery_response',
             'is_success', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']