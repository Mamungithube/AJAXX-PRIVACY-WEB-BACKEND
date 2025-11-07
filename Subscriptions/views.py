from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import stripe
import json

from .models import Subscription, Payment, UserSubscription
from .serializers import (
    SubscriptionSerializer, PaymentSerializer, 
    PaymentCreateSerializer, SavePaymentSerializer
)
from .utils import send_payment_email

stripe.api_key = settings.STRIPE_SECRET_KEY


from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework import status


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
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
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
                        'unit_amount': int(subscription.price * 100),  # Convert to cents
                        'product_data': {
                            'name': subscription.title,
                            'description': subscription.short_description,
                        },
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=request.build_absolute_uri('/payment-success/') + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=request.build_absolute_uri('/payment-cancel/'),
                client_reference_id=str(request.user.id),
                metadata={
                    'subscription_id': subscription_id,
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
        
        except stripe.error.StripeError as e:
            return Response({
                'success': False,
                'message': 'Failed to create checkout session',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='verify-payment')
    def verify_payment(self, request):
        """Verify Payment After Checkout Success"""
        session_id = request.query_params.get('session_id')
        
        if not session_id:
            return Response({
                'success': False,
                'message': 'Session ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Retrieve checkout session from Stripe
            session = stripe.checkout.Session.retrieve(session_id)
            
            if session.payment_status != 'paid':
                return Response({
                    'success': False,
                    'message': 'Payment not completed'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get subscription and user info
            subscription_id = session.metadata.get('subscription_id')
            user_id = session.metadata.get('user_id')
            
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
                'message': 'Failed to verify payment',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
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
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
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
        start_date = start_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
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


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def stripe_webhook(request):

    """----------Handle Stripe Webhooks-----------"""

    
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        return Response({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError:
        return Response({'error': 'Invalid signature'}, status=400)
    
    # Handle checkout session completed
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        if session.payment_status == 'paid':
            try:
                subscription_id = session.metadata.get('subscription_id')
                user_id = session.metadata.get('user_id')
                
                subscription = Subscription.objects.get(id=subscription_id)
                
                # Calculate validity
                now = timezone.now()
                if subscription.billing_cycle == 'monthly':
                    valid_till = now + relativedelta(months=1)
                else:
                    valid_till = now + relativedelta(years=1)
                
                # Save payment
                Payment.objects.create(
                    user_id=user_id,
                    subscription=subscription,
                    amount=session.amount_total / 100,
                    transaction_id=session.payment_intent,
                    invoice_id=session.invoice or Payment.generate_invoice_id(),
                    status='succeeded',
                    payment_date=now
                )
                
                # Update user subscription
                UserSubscription.objects.update_or_create(
                    user_id=user_id,
                    defaults={
                        'plan': subscription,
                        'starts_at': now,
                        'expires_at': valid_till,
                        'status': 'active'
                    }
                )
            except Exception as e:
                print(f"Webhook error: {e}")
    
    # Handle payment intent events (for backward compatibility)
    elif event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        
        try:
            payment = Payment.objects.get(transaction_id=payment_intent['id'])
            payment.status = 'succeeded'
            payment.save()
        except Payment.DoesNotExist:
            pass
    
    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        
        try:
            payment = Payment.objects.get(transaction_id=payment_intent['id'])
            payment.status = 'failed'
            payment.save()
        except Payment.DoesNotExist:
            pass
    
    return Response({'received': True})