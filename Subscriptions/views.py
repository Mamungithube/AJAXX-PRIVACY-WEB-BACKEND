from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from django.shortcuts import get_object_or_404
from .models import Plan, Subscription
from .serializers import PlanSerializer, SubscriptionSerializer
import stripe
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from datetime import datetime

stripe.api_key = settings.STRIPE_SECRET_KEY

class PlanListAPIView(APIView):
    def get(self, request):
        plans = Plan.objects.all()
        serializer = PlanSerializer(plans, many=True)
        return Response(serializer.data)

class CreateCheckoutSession(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, price_id):
        try:
            plan = get_object_or_404(Plan, stripe_price_id=price_id)
            
            # Check if user already has an active subscription
            existing_sub = Subscription.objects.filter(
                user=request.user, 
                status__in=['active', 'trialing']
            ).first()
            
            if existing_sub:
                return Response(
                    {"error": "You already have an active subscription"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create Stripe checkout session
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=settings.FRONTEND_URL + '/success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=settings.FRONTEND_URL + '/cancel',
                customer_email=request.user.email,
                metadata={
                    'user_id': str(request.user.id),
                    'plan_id': str(plan.id)
                }
            )
            
            return Response({
                "checkout_url": session.url,
                "session_id": session.id
            })
            
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

class CreatePortalSession(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            subscription = get_object_or_404(
                Subscription, 
                user=request.user, 
                status__in=['active', 'trialing']
            )
            
            if not subscription.stripe_customer_id:
                return Response(
                    {"error": "No customer ID found"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            session = stripe.billing_portal.Session.create(
                customer=subscription.stripe_customer_id,
                return_url=settings.FRONTEND_URL + '/subscription',
            )
            
            return Response({"portal_url": session.url})
            
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

class UserSubscriptionAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        subscription = Subscription.objects.filter(user=request.user).first()
        if subscription:
            serializer = SubscriptionSerializer(subscription)
            return Response(serializer.data)
        return Response({"detail": "No subscription found"})

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_checkout_session_completed(session)
        
    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        handle_subscription_updated(subscription)
        
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        handle_subscription_deleted(subscription)

    return HttpResponse(status=200)

def handle_checkout_session_completed(session):
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        user_id = session['metadata']['user_id']
        plan_id = session['metadata']['plan_id']
        stripe_subscription_id = session['subscription']
        stripe_customer_id = session['customer']
        
        user = User.objects.get(id=user_id)
        plan = Plan.objects.get(id=plan_id)
        
        # Get subscription details from Stripe
        stripe_sub = stripe.Subscription.retrieve(stripe_subscription_id)
        
        # Create or update subscription
        subscription, created = Subscription.objects.update_or_create(
            user=user,
            defaults={
                'plan': plan,
                'stripe_subscription_id': stripe_subscription_id,
                'stripe_customer_id': stripe_customer_id,
                'status': stripe_sub['status'],
                'current_period_start': datetime.fromtimestamp(stripe_sub['current_period_start']),
                'current_period_end': datetime.fromtimestamp(stripe_sub['current_period_end']),
            }
        )
        
        print(f"Subscription created/updated for {user.email}")
        
    except Exception as e:
        print(f"Error handling checkout session: {str(e)}")

def handle_subscription_updated(subscription):
    try:
        sub = Subscription.objects.get(stripe_subscription_id=subscription['id'])
        sub.status = subscription['status']
        sub.current_period_start = datetime.fromtimestamp(subscription['current_period_start'])
        sub.current_period_end = datetime.fromtimestamp(subscription['current_period_end'])
        sub.save()
        
        print(f"Subscription updated: {sub.id} - {sub.status}")
        
    except Subscription.DoesNotExist:
        print(f"Subscription not found: {subscription['id']}")
    except Exception as e:
        print(f"Error updating subscription: {str(e)}")

def handle_subscription_deleted(subscription):
    try:
        sub = Subscription.objects.get(stripe_subscription_id=subscription['id'])
        sub.status = 'canceled'
        sub.save()
        
        print(f"Subscription canceled: {sub.id}")
        
    except Subscription.DoesNotExist:
        print(f"Subscription not found: {subscription['id']}")
    except Exception as e:
        print(f"Error canceling subscription: {str(e)}")