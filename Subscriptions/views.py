from django.shortcuts import render
from rest_framework.exceptions import NotFound
from .serializers import (
    SubscriptionSerializer, PaymentSerializer,
    PaymentCreateSerializer, SavePaymentSerializer
)
from stripe import StripeError
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.conf import settings
from django.db.models import Sum
from django.utils import timezone
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import stripe
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from rest_framework.permissions import AllowAny
from django.conf import settings
import logging

from .models import Subscription, Payment, UserSubscription
from .utils import send_payment_email

logger = logging.getLogger(__name__)


stripe.api_key = settings.STRIPE_SECRET_KEY
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response



@api_view(['GET'])
@permission_classes([AllowAny])
def verify_payment_public(request):
    """Verify Payment - Public Access (No Authentication Required)"""
    print("🔍 Verifying payment (Public)...")
    session_id = request.query_params.get('session_id')
    print(f"🔑 Session ID: {session_id}")

    if not session_id:
        return Response({
            'success': False,
            'message': 'Session ID is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Session validation
        if not session_id.startswith('cs_test_'):
            return Response({
                'success': False,
                'message': 'Invalid session ID format'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve checkout session from Stripe
        session = stripe.checkout.Session.retrieve(session_id)
        print(f"💰 Stripe Session Status: {session.payment_status}")
        print(f"👤 User ID from metadata: {session.metadata.get('user_id')}")
        print(f"📦 Subscription ID from metadata: {session.metadata.get('subscription_id')}")

        if session.payment_status != 'paid':
            return Response({
                'success': False,
                'message': 'Payment not completed'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get subscription and user info
        subscription_id = session.metadata.get('subscription_id')
        user_id = session.metadata.get('user_id')

        if not subscription_id or not user_id:
            return Response({
                'success': False,
                'message': 'Missing user or subscription information in session'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check for duplicate payment
        existing_payment = Payment.objects.filter(transaction_id=session.payment_intent).first()
        if existing_payment:
            print("🔄 Payment already exists, returning existing data")
            return Response({
                'success': True,
                'message': 'Payment already verified',
                'data': PaymentSerializer(existing_payment).data
            })

        subscription = Subscription.objects.get(id=subscription_id)

        # Calculate validity dates
        now = timezone.now()
        if subscription.billing_cycle == 'monthly':
            valid_till = now + relativedelta(months=1)
        else:  # yearly
            valid_till = now + relativedelta(years=1)

        # Save payment
        payment = Payment.objects.create(
            user_id=user_id,
            subscription=subscription,
            amount=session.amount_total / 100,  # Convert from cents
            transaction_id=session.payment_intent,
            invoice_id=session.invoice or Payment.generate_invoice_id(),
            status='succeeded',
            payment_date=now
        )

        # Update or create user subscription
        UserSubscription.objects.update_or_create(
            user_id=user_id,
            defaults={
                'plan': subscription,
                'starts_at': now,
                'expires_at': valid_till,
                'status': 'active'
            }
        )

        # Send email confirmation
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(id=user_id)

        send_payment_email(
            email=user.email,
            amount=payment.amount,
            transaction_id=payment.transaction_id,
            invoice_id=payment.invoice_id,
            payment_status='succeeded'
        )

        print(f"✅ Payment verified successfully! Payment ID: {payment.id}")

        return Response({
            'success': True,
            'message': 'Payment verified successfully',
            'data': PaymentSerializer(payment).data
        })

    except Subscription.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Subscription plan not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except stripe.error.StripeError as e:
        return Response({
            'success': False,
            'message': 'Failed to verify payment with Stripe',
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print(f"🔴 Unexpected error: {str(e)}")
        return Response({
            'success': False,
            'message': 'Internal server error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def payment_success_page(request):
    """Render payment success page"""
    return render(request, 'payments/payment-success.html')


def payment_failed_page(request):
    """Render payment failed page"""
    return render(request, 'payments/payment-failed.html')


class SubscriptionViewSet(viewsets.ModelViewSet):
    """Subscription CRUD Operations"""

    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [permission() for permission in self.permission_classes]

    def get_object(self):
        """Override to provide custom error message"""
        try:
            return super().get_object()
        except Subscription.DoesNotExist:
            raise NotFound({
                'success': False,
                'message': 'Subscription not found',
                'data': None
            })

    def list(self, request, *args, **kwargs):
        """List all subscriptions"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        return Response({
            'success': True,
            'message': 'Subscriptions retrieved successfully',
            'data': serializer.data
        })

    def retrieve(self, request, *args, **kwargs):
        """Get single subscription"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        return Response({
            'success': True,
            'message': 'Subscription retrieved successfully',
            'data': serializer.data
        })

    def create(self, request, *args, **kwargs):
        """Create Subscription Plan"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        subscription = serializer.save()

        return Response({
            'success': True,
            'message': 'Subscription created successfully',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Update Subscription Plan"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        subscription = serializer.save()

        return Response({
            'success': True,
            'message': 'Subscription updated successfully',
            'data': serializer.data
        })

    def destroy(self, request, *args, **kwargs):
        """Delete Subscription Plan"""
        instance = self.get_object()
        plan_name = instance.title
        instance.delete()

        return Response({
            'success': True,
            'message': f'Subscription "{plan_name}" deleted successfully',
            'data': None
        }, status=status.HTTP_200_OK)


class PaymentViewSet(viewsets.ModelViewSet):

    """------------Payment Operations----------"""
    UUID_MAPPING = {
        15: '8e88f2ce-8822-487f-9017-e75cded09a8a',
        16: '8f48c726-728b-49cc-88fe-a8e3425f0594',
        17: '97f094f2-e5d7-4b6b-b8ca-a8f82e80eaf5',
        19: 'a27c44c3-6029-4a6d-83bd-c43365b0a2df',
    }
    queryset = Payment.objects.select_related('user', 'subscription').all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'total_earnings', 'todays_earnings',
                           'monthly_stats', 'earnings_overview']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['post'], url_path='create-checkout-session')
    def create_checkout_session(self, request):
        """Create Stripe Checkout Session"""
        subscription_id = request.data.get('subscription_id')

        if not subscription_id:
            return Response({
                'success': False,
                'message': 'Subscription ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            subscription = Subscription.objects.get(id=subscription_id)
        except Subscription.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Subscription plan not found'
            }, status=status.HTTP_404_NOT_FOUND)

        try:
            # Create Stripe Checkout Session
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        # Convert to cents
                        'unit_amount': int(subscription.price * 100),
                        'product_data': {
                            'name': subscription.title,
                            'description': subscription.Description,
                        },
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=request.build_absolute_uri(
                    '/payment/success/') + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=request.build_absolute_uri('/payment/failed/'),
                client_reference_id=str(request.user.id),
                metadata={
                    'subscription_id': str(subscription_id),
                    'user_id': request.user.id,
                }
            )

            return Response({
                'success': True,
                'message': 'Checkout session created',
                'data': {
                    'session_id': checkout_session.id,
                    'checkout_url': checkout_session.url
                }
            })

        except stripe.StripeError as e:  # FIXED: removed .error
            return Response({
                'success': False,
                'message': 'Failed to create checkout session',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    @action(detail=False, methods=['get'], url_path='total-earnings')
    def total_earnings(self, request):
        """-------------------Get Total Earnings----------------------"""

        total = Payment.objects.filter(status='succeeded').aggregate(
            total=Sum('amount')
        )['total'] or 0

        return Response({
            'success': True,
            'message': 'Total earnings fetched successfully',
            'data': {'total': float(total)}
        })

    @action(detail=False, methods=['get'], url_path='todays-earnings')
    def todays_earnings(self, request):
        """Get Today's Earnings"""
        today = timezone.now().date()
        tomorrow = today + timedelta(days=1)

        total = Payment.objects.filter(
            status='succeeded',
            payment_date__gte=today,
            payment_date__lt=tomorrow
        ).aggregate(total=Sum('amount'))['total'] or 0

        return Response({
            'success': True,
            'message': "Today's earnings fetched successfully",
            'data': {'total': float(total)}
        })

    @action(detail=False, methods=['get'], url_path='monthly-stats')
    def monthly_stats(self, request):
        """------------Get Monthly Earnings Stats with Growth Percentage----------"""

        now = timezone.now()
        current_month_start = now.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0)
        previous_month_start = (current_month_start - relativedelta(months=1))

        # Current month earnings
        current_earnings = Payment.objects.filter(
            status='succeeded',
            payment_date__gte=current_month_start
        ).aggregate(total=Sum('amount'))['total'] or 0

        # Previous month earnings
        previous_earnings = Payment.objects.filter(
            status='succeeded',
            payment_date__gte=previous_month_start,
            payment_date__lt=current_month_start
        ).aggregate(total=Sum('amount'))['total'] or 0

        # Calculate percentage change
        difference = float(current_earnings) - float(previous_earnings)
        if previous_earnings > 0:
            percentage_change = (difference / float(previous_earnings)) * 100
        elif current_earnings > 0:
            percentage_change = 100
        else:
            percentage_change = 0

        return Response({
            'success': True,
            'message': 'Monthly earnings stats fetched successfully',
            'data': {
                'current_earnings': float(current_earnings),
                'previous_earnings': float(previous_earnings),
                'percentage_change': round(percentage_change, 2),
                'trend': 'up' if percentage_change >= 0 else 'down'
            }
        })

    @action(detail=False, methods=['get'], url_path='earnings-overview')
    def earnings_overview(self, request):
        """Get 12 Months Earnings Overview"""
        year = request.query_params.get('year')

        if year:
            base_date = datetime(int(year), 12, 31)
        else:
            base_date = timezone.now()

        # Get earnings for last 12 months
        start_date = base_date - relativedelta(months=11)
        start_date = start_date.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0)

        earnings_data = []
        for i in range(12):
            month_date = start_date + relativedelta(months=i)
            next_month = month_date + relativedelta(months=1)

            total = Payment.objects.filter(
                status='succeeded',
                payment_date__gte=month_date,
                payment_date__lt=next_month
            ).aggregate(total=Sum('amount'))['total'] or 0

            earnings_data.append({
                'month': month_date.strftime('%b'),
                'total': float(total)
            })

        # Calculate growth percentage
        first_month = earnings_data[0]['total']
        last_month = earnings_data[-1]['total']

        difference = last_month - first_month
        if first_month > 0:
            growth_percentage = (difference / first_month) * 100
        elif last_month > 0:
            growth_percentage = 100
        else:
            growth_percentage = 0

        return Response({
            'success': True,
            'message': '12-month earnings overview fetched successfully',
            'data': {
                'earnings': earnings_data,
                'growth_percentage': round(growth_percentage, 2),
                'trend': 'up' if growth_percentage >= 0 else 'down'
            }
        })

    @action(detail=False, methods=['get'], url_path='current-subscription')
    def current_subscription(self, request):
        """
        Retrieves the authenticated user's current active subscription plan
        and includes a specific UUID based on the plan ID (15, 16, 17, or 18).
        """
        user = request.user
        
        try:
            # 1. Get the user's active subscription record
            user_subscription = UserSubscription.objects.get(
                user=user,
                status='active' 
            )
            
            # 2. Get the subscription plan details
            subscription = user_subscription.plan
            plan_data = SubscriptionSerializer(subscription).data
            
            # 3. APPLY CUSTOM UUID LOGIC HERE
            plan_id = subscription.id
            
            # Check if the plan_id is in the defined mapping
            specific_uuid = self.UUID_MAPPING.get(plan_id)
            
            # 4. Construct the final response data
            response_data = {
                'plan': plan_data,
                'starts_at': user_subscription.starts_at,
                'expires_at': user_subscription.expires_at,
                'status': user_subscription.status,
                # Add the custom UUID field
                'plan_uuid': specific_uuid
            }
            
            return Response({
                'success': True,
                'message': 'Current active subscription fetched successfully with custom UUID',
                'data': response_data
            })
            
        except UserSubscription.DoesNotExist:
            return Response({
                'success': False,
                'message': 'No active subscription found for this user',
                'data': None
            }, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            logger.error(f"Error fetching current subscription for user {user.id}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Internal server error while fetching subscription',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def stripe_webhook(request):
    """----------Handle Stripe Webhooks-----------"""
    if request.content_type == 'application/json':
        data = json.loads(request.body)
        event_type = data.get('type')
        session = data.get('data', {}).get('object', {})

        if event_type == 'checkout.session.completed':
            return handle_checkout_session_completed(session)

    print("🔔 Webhook received - Starting processing...")

    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    if not webhook_secret:
        logger.error("❌ STRIPE_WEBHOOK_SECRET is not set in settings")
        return JsonResponse({'error': 'Webhook secret not configured'}, status=500)

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
        print(f"✅ Event constructed: {event['type']}")
    except ValueError as e:
        logger.error(f"❌ Invalid payload: {e}")
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"❌ Invalid signature: {e}")
        return JsonResponse({'error': 'Invalid signature'}, status=400)
    except Exception as e:
        logger.error(f"❌ Webhook construction error: {e}")
        return JsonResponse({'error': 'Webhook processing failed'}, status=400)

    # Handle checkout session completed
    if event['type'] == 'checkout.session.completed':
        print("🛒 Processing checkout.session.completed event")
        return handle_checkout_session_completed(event['data']['object'])

    # Handle payment intent events
    elif event['type'] == 'payment_intent.succeeded':
        print("💳 Processing payment_intent.succeeded event")
        return handle_payment_intent_succeeded(event['data']['object'])

    elif event['type'] == 'payment_intent.payment_failed':
        print("❌ Processing payment_intent.payment_failed event")
        return handle_payment_intent_failed(event['data']['object'])

    else:
        print(f"Unhandled event type: {event['type']}")

    return JsonResponse({'received': True})


def handle_checkout_session_completed(session):
    """Handle completed checkout session"""
    try:
        print(f"🔍 Session details: {session}")

        # Check if payment is successful
        if session.payment_status != 'paid':
            print(
                f"⚠️ Payment not completed. Status: {session.payment_status}")
            return JsonResponse({'received': True})

        # Extract metadata
        subscription_id = session.metadata.get('subscription_id')
        user_id = session.metadata.get('user_id')

        print(
            f"📋 Metadata - subscription_id: {subscription_id}, user_id: {user_id}")

        if not subscription_id or not user_id:
            print("❌ Missing required metadata in session")
            return JsonResponse({'error': 'Missing metadata'}, status=400)

        # Check if payment already exists to avoid duplicates
        existing_payment = Payment.objects.filter(
            transaction_id=session.payment_intent).first()
        if existing_payment:
            print(
                f"✅ Payment already exists in database: {existing_payment.id}")
            return JsonResponse({'received': True})

        # Get subscription
        try:
            subscription = Subscription.objects.get(id=subscription_id)
            print(f"📦 Subscription found: {subscription.title}")
        except Subscription.DoesNotExist:
            print(f"❌ Subscription not found: {subscription_id}")
            return JsonResponse({'error': 'Subscription not found'}, status=404)

        # Calculate validity dates
        now = timezone.now()
        if subscription.billing_cycle == 'monthly':
            valid_till = now + relativedelta(months=1)
        else:  # yearly
            valid_till = now + relativedelta(years=1)

        print(f"📅 Validity calculated: {valid_till}")

        # Create payment record
        try:
            payment = Payment.objects.create(
                user_id=user_id,
                subscription=subscription,
                amount=session.amount_total / 100,  # Convert from cents
                transaction_id=session.payment_intent,
                invoice_id=session.invoice or Payment.generate_invoice_id(),
                status='succeeded',
                payment_date=now
            )
            print(f"💰 Payment created successfully: {payment.id}")
        except Exception as e:
            print(f"❌ Payment creation failed: {e}")
            return JsonResponse({'error': 'Payment creation failed'}, status=500)

        # Update or create user subscription
        try:
            user_subscription, created = UserSubscription.objects.update_or_create(
                user_id=user_id,
                defaults={
                    'plan': subscription,
                    'starts_at': now,
                    'expires_at': valid_till,
                    'status': 'active'
                }
            )
            action = "created" if created else "updated"
            print(f"👤 User subscription {action}: {user_subscription.id}")
        except Exception as e:
            print(f"❌ User subscription update failed: {e}")
            # Don't return error here, just log it

        # Send email confirmation
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=user_id)

            send_payment_email(
                email=user.email,
                amount=payment.amount,
                transaction_id=payment.transaction_id,
                invoice_id=payment.invoice_id,
                payment_status='succeeded'
            )
            print(f"📧 Email sent to: {user.email}")
        except Exception as e:
            print(f"⚠️ Email sending failed: {e}")
            # Continue even if email fails

        print("✅ Checkout session processing completed successfully")
        return JsonResponse({'received': True})

    except Exception as e:
        logger.error(f"❌ Error in handle_checkout_session_completed: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': 'Processing failed'}, status=500)


def handle_payment_intent_succeeded(payment_intent):
    """Handle successful payment intent"""
    try:
        print(f"🔍 Payment Intent: {payment_intent['id']}")

        # Check if payment already exists
        existing_payment = Payment.objects.filter(
            transaction_id=payment_intent['id']).first()
        if existing_payment:
            print(f"🔄 Updating existing payment: {existing_payment.id}")
            existing_payment.status = 'succeeded'
            existing_payment.save()
            print(f"✅ Payment updated: {existing_payment.id}")
        else:
            print(f" No existing payment found for: {payment_intent['id']}")

        return JsonResponse({'received': True})

    except Exception as e:
        logger.error(f"❌ Error in handle_payment_intent_succeeded: {str(e)}")
        return JsonResponse({'error': 'Payment intent processing failed'}, status=500)


def handle_payment_intent_failed(payment_intent):
    """Handle failed payment intent"""
    try:
        print(f"🔍 Failed Payment Intent: {payment_intent['id']}")

        # Update existing payment if found
        existing_payment = Payment.objects.filter(
            transaction_id=payment_intent['id']).first()
        if existing_payment:
            existing_payment.status = 'failed'
            existing_payment.save()
            print(f"❌ Payment marked as failed: {existing_payment.id}")

        return JsonResponse({'received': True})

    except Exception as e:
        logger.error(f"❌ Error in handle_payment_intent_failed: {str(e)}")
        return JsonResponse({'error': 'Payment intent processing failed'}, status=500)
