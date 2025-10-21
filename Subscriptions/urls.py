from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SubscriptionViewSet, PaymentViewSet, stripe_webhook

# Router automatically creates standard REST endpoints
router = DefaultRouter()
router.register('subscriptions', SubscriptionViewSet, basename='subscription')
router.register('payments', PaymentViewSet, basename='payment')

# Router automatically generates these endpoints:
# 
# SUBSCRIPTIONS:
# GET    /subscriptions/           - List all subscriptions
# POST   /subscriptions/           - Create subscription (Admin)
# GET    /subscriptions/{id}/      - Get single subscription
# PUT    /subscriptions/{id}/      - Update subscription (Admin)
# PATCH  /subscriptions/{id}/      - Partial update (Admin)
# DELETE /subscriptions/{id}/      - Delete subscription (Admin)
#
# PAYMENTS:
# GET    /payments/                - List all payments (Admin)
# POST   /payments/                - Create payment
# GET    /payments/{id}/           - Get single payment (Admin)
# PUT    /payments/{id}/           - Update payment
# PATCH  /payments/{id}/           - Partial update
# DELETE /payments/{id}/           - Delete payment
#
# CUSTOM ACTIONS (@action decorators):
# POST   /payments/create-checkout-session/     - Create Stripe Checkout Session
# GET    /payments/verify-payment/?session_id=  - Verify payment after success
# GET    /payments/total-earnings/              - Total earnings (Admin)
# GET    /payments/todays-earnings/             - Today's earnings (Admin)
# GET    /payments/monthly-stats/               - Monthly stats (Admin)
# GET    /payments/earnings-overview/           - 12 month overview (Admin)

urlpatterns = [
    # Stripe webhook (must be before router)
    path('webhook/', stripe_webhook, name='stripe-webhook'),
    
    # All router-generated URLs
    path('', include(router.urls)),
]

# Final URL structure:
# /api/payments/webhook/
# /api/payments/subscriptions/
# /api/payments/subscriptions/{id}/
# /api/payments/payments/
# /api/payments/payments/{id}/
# /api/payments/payments/create-checkout-session/
# /api/payments/payments/verify-payment/?session_id=xxx
# /api/payments/payments/total-earnings/
# /api/payments/payments/todays-earnings/
# /api/payments/payments/monthly-stats/
# /api/payments/payments/earnings-overview/