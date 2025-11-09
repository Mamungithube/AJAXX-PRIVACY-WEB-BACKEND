from django.contrib import admin
from .models import Subscription, Payment, UserSubscription

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['title', 'price', 'billing_cycle', 'created_at']
    search_fields = ['title']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'status', 'payment_date']
    list_filter = ['status', 'payment_date']
    search_fields = ['transaction_id', 'user__email']

@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'status', 'expires_at']
    list_filter = ['status']

    