# Assuming your app is named 'membership' or similar
from rest_framework import serializers
from .models import add_member

class AddMemberSerializer(serializers.ModelSerializer):

    class Meta:
        model = add_member
        fields = '__all__'
