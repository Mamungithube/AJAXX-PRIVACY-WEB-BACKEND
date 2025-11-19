from rest_framework import serializers
from .models import Subscription, Payment, UserSubscription,Feature
from django.contrib.auth import get_user_model
User = get_user_model()


class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = ['id', 'description']


class SubscriptionSerializer(serializers.ModelSerializer):
    features = FeatureSerializer(many=True)

    class Meta:
        model = Subscription
        fields = [
            'id', 'title', 'Description', 'price',
            'billing_cycle', 'features'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        features_data = validated_data.pop('features', [])
        subscription = Subscription.objects.create(**validated_data)
        
        # প্রতিটা feature আলাদা করে create হবে
        for feature_data in features_data:
            feature = Feature.objects.create(**feature_data)
            subscription.features.add(feature)
        
        return subscription

    def update(self, instance, validated_data):
        features_data = validated_data.pop('features', None)
        
        # Update subscription fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update features
        if features_data is not None:
            # পুরাতন features clear করে নতুন add করবে
            instance.features.clear()
            for feature_data in features_data:
                feature = Feature.objects.create(**feature_data)
                instance.features.add(feature)
        
        return instance
        
        return instance
class UserBasicSerializer(serializers.ModelSerializer):
    """Basic User Info for Payment"""
    class Meta:
        model = User
        fields = "__all__"


class PaymentSerializer(serializers.ModelSerializer):
    """Payment Serializer with Relations"""
    user = UserBasicSerializer(read_only=True)
    subscription = SubscriptionSerializer(read_only=True)
    subscription_id = serializers.PrimaryKeyRelatedField(
        queryset=Subscription.objects.all(), 
        source='subscription', 
        write_only=True
    )
    
    class Meta:
        model = Payment
        fields = ['id', 'user', 'subscription', 'subscription_id', 'amount', 
                  'transaction_id', 'invoice_id', 'status', 'payment_date', 
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'payment_date', 'created_at', 'updated_at']


class PaymentCreateSerializer(serializers.Serializer):
    """Serializer for Creating Checkout Session"""
    subscription_id = serializers.IntegerField()
    
    def validate_subscription_id(self, value):
        if not Subscription.objects.filter(id=value).exists():
            raise serializers.ValidationError("Subscription plan not found")
        return value


class SavePaymentSerializer(serializers.Serializer):
    """Serializer for Verifying Payment (Not needed for Checkout Session)"""
    session_id = serializers.CharField(max_length=255)


class VerifyPaymentSerializer(serializers.Serializer):
    """Serializer for Payment Verification"""
    session_id = serializers.CharField(max_length=255, required=True)


class UserSubscriptionSerializer(serializers.ModelSerializer):
    """User Subscription Serializer"""
    plan = SubscriptionSerializer(read_only=True)
    
    class Meta:
        model = UserSubscription
        fields = ['id', 'plan', 'starts_at', 'expires_at', 'status', 
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']