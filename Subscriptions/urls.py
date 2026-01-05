from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (SubscriptionViewSet, 
                    PaymentViewSet,
                    cancel_user_subscription,
                    reactivate_user_subscription, 
                    stripe_webhook ,
                    payment_success_page, 
                    payment_failed_page,
                    verify_payment_public,
                    create_checkout_session,
                    get_current_subscription
)
# Router automatically creates standard REST endpoints
router = DefaultRouter()
router.register('subscriptions', SubscriptionViewSet, basename='subscription')
router.register('payments', PaymentViewSet, basename='payment')

urlpatterns = [
    # Stripe webhook (must be before router)
    path('webhook/', stripe_webhook, name='stripe-webhook'),
    path('verify-payment/', verify_payment_public, name='verify-payment-public'),
    # All router-generated URLs
    path('', include(router.urls)),
    path('success/', payment_success_page, name='payment-success'),
    path('failed/', payment_failed_page, name='payment-failed'),
    path('create-checkout-session/', create_checkout_session, name='create-checkout-session'),
    path('current-subscription/', get_current_subscription, name='current-subscription'),

    path('cancel-subscription/', cancel_user_subscription, name='cancel-subscription'),
    path('reactivate-subscription/', reactivate_user_subscription, name='reactivate-subscription')
]

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