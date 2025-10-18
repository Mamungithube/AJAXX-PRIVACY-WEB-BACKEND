from rest_framework import serializers
from . import models

class ContactUsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ContactUs
        fields = '__all__'


class ReviewSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.CharField(source='reviewer.username', read_only=True)

    class Meta:
        model = models.Review
        fields = ['id', 'body', 'created', 'rating', 'reviewer', 'reviewer_name']
        extra_kwargs = {'reviewer': {'required': False}}  # Allow it to be auto-set

    def create(self, validated_data):
        validated_data['reviewer'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['reviewer'] = instance.reviewer  # Prevent reviewer change
        return super().update(instance, validated_data)