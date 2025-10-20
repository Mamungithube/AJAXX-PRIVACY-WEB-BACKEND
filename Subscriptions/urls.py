
from django.urls import path
from .views import (
    PlanListAPIView, 
    CreateCheckoutSession, 
    stripe_webhook,
    CreatePortalSession,
    UserSubscriptionAPIView
)

urlpatterns = [
    path('plans/', PlanListAPIView.as_view(), name='plan-list'),
    path('create-checkout-session/<str:price_id>/', CreateCheckoutSession.as_view(), name='create-checkout-session'),
    path('create-portal-session/', CreatePortalSession.as_view(), name='create-portal-session'),
    path('my-subscription/', UserSubscriptionAPIView.as_view(), name='my-subscription'),
    path('webhook/stripe/', stripe_webhook, name='stripe-webhook'),
]

