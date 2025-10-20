# subscriptions/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone

class Plan(models.Model):
    name = models.CharField(max_length=50, unique=True, blank=True, null=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    stripe_price_id = models.CharField(max_length=100, blank=True, null=True)
    stripe_product_id = models.CharField(max_length=100, blank=True, null=True)
    interval = models.CharField(max_length=20, default='month')
    
    # Plan features
    identities_limit = models.IntegerField(default=10)
    scans_per_month = models.IntegerField(default=10)
    automated_data_removal = models.BooleanField(default=True)
    pdf_export_limit = models.IntegerField(null=True, blank=True)
    support_hours = models.CharField(max_length=50, default='24-48h')
    
    def __str__(self):
        return self.name if self.name else f"Plan {self.id}"


class Subscription(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('past_due', 'Past Due'),
        ('canceled', 'Canceled'),
        ('trialing', 'Trialing'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    stripe_subscription_id = models.CharField(max_length=100, unique=True, blank=True, null=True)
    stripe_customer_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='inactive')
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.plan.name}"