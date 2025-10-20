# subscriptions/admin.py
from django.contrib import admin
from .models import Plan, Subscription

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'interval', 'identities_limit', 'scans_per_month']
    list_editable = ['price', 'identities_limit', 'scans_per_month']

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'status', 'current_period_end']
    list_filter = ['status', 'plan']
    search_fields = ['user__email', 'stripe_subscription_id']