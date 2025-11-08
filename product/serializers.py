# serializers.py
from rest_framework import serializers
from .models import Product
from decimal import Decimal

class ProductSerializer(serializers.ModelSerializer):
    dynamic_discount_percentage = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'title',
            'description',
            'old_price',
            'new_price',
            'billing_cycle',
            'add_link',
            'created_at',
            'dynamic_discount_percentage',
        ]
        read_only_fields = ('created_at',)

    def get_dynamic_discount_percentage(self, obj):

        try:
            old_price = obj.old_price
            new_price = obj.new_price
            if old_price > Decimal(0):
                price_difference = old_price - new_price
                percentage = (price_difference / old_price) * 100
                return percentage.quantize(Decimal('0.00'))
            return Decimal(0)
            
        except (TypeError, AttributeError):
              return Decimal(0)
        
        super().save(*args, **kwargs)

def __str__(self):
        return self.title
