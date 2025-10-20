from rest_framework import serializers
from .models import Plan, Subscription

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ['id', 'name', 'description', 'price', 'interval', 
                  'identities_limit', 'scans_per_month', 'automated_data_removal', 
                  'pdf_export_limit', 'support_hours']
        # Exclude stripe_product_id and stripe_price_id from frontend

class SubscriptionSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    plan_details = PlanSerializer(source='plan', read_only=True)
    
    class Meta:
        model = Subscription
        fields = '__all__'