from django.shortcuts import render
from rest_framework.exceptions import NotFound
from .serializers import (
    SubscriptionSerializer, PaymentSerializer,
    PaymentCreateSerializer, SavePaymentSerializer
)
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.conf import settings
from django.db.models import Sum
from django.utils import timezone
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import stripe
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
import logging

from .models import Subscription, Payment, UserSubscription
from .utils import send_payment_email

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY
# views.py তে এই function টা যোগ করুন (PaymentViewSet এর বাইরে)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_checkout_session(request):
    """
    🔥 STRIPE CHECKOUT (SUBSCRIPTION)
    Creates a Stripe checkout session for subscription payment
    """
    print("=" * 80)
    print("🚀 CREATE CHECKOUT SESSION STARTED")
    print("=" * 80)
    
    subscription_id = request.data.get('subscription_id')
    print(f"📦 Received subscription_id: {subscription_id}")
    
    if not subscription_id:
        print("❌ No subscription_id provided")
        return Response({
            'success': False,
            'message': 'Subscription ID required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        subscription = Subscription.objects.get(id=subscription_id)
        print(f"✅ Subscription found: {subscription.title}")
        print(f"💰 Price: ${subscription.price}")
        print(f"📅 Billing cycle: {subscription.billing_cycle}")
    except Subscription.DoesNotExist:
        print(f"❌ Subscription not found with id: {subscription_id}")
        return Response({
            'success': False,
            'message': 'Subscription not found'
        }, status=status.HTTP_404_NOT_FOUND)

    try:
        # Check current Stripe field values
        print(f"📊 Current Stripe values:")
        print(f"   - stripe_product_id: {subscription.stripe_product_id}")
        print(f"   - stripe_price_id: {subscription.stripe_price_id}")
        
        # Check if Stripe Price ID already exists
        if subscription.stripe_price_id:
            stripe_price_id = subscription.stripe_price_id
            print(f"✅ Using existing Stripe Price ID: {stripe_price_id}")
        else:
            print(f"🔧 Creating NEW Stripe Product and Price...")
            
            # Create or get Stripe Product
            if subscription.stripe_product_id:
                stripe_product_id = subscription.stripe_product_id
                print(f"✅ Using existing Stripe Product ID: {stripe_product_id}")
            else:
                print(f"🆕 Creating Stripe Product: {subscription.title}")
                
                stripe_product = stripe.Product.create(
                    name=subscription.title,
                    description=subscription.Description[:500] if len(subscription.Description) > 500 else subscription.Description,
                )
                stripe_product_id = stripe_product.id
                subscription.stripe_product_id = stripe_product_id
                subscription.save()
                
                print(f"✅ Created Stripe Product: {stripe_product_id}")
            
            # Create Stripe Price
            price_amount = int(float(subscription.price) * 100)
            print(f"🆕 Creating Stripe Price: ${subscription.price} ({price_amount} cents)")
            
            stripe_price = stripe.Price.create(
                product=stripe_product_id,
                unit_amount=price_amount,
                currency='usd',
                recurring={
                    'interval': 'month' if subscription.billing_cycle == 'monthly' else 'year'
                }
            )
            stripe_price_id = stripe_price.id
            subscription.stripe_price_id = stripe_price_id
            subscription.save()
            
            print(f"✅ Created Stripe Price: {stripe_price_id}")
            print(f"💾 Saved to database")

        # 🔥 CRITICAL FIX: Build URL properly
        # Method 1: String concatenation (no f-string)
        base_url = request.build_absolute_uri('/payment/success/')
        success_url = base_url + '?session_id={CHECKOUT_SESSION_ID}'
        
        cancel_url = request.build_absolute_uri('/payment/failed/')
        
        print(f"🔗 URLs created:")
        print(f"   - Success: {success_url}")
        print(f"   - Cancel: {cancel_url}")

        # Create Stripe checkout session
        print(f"🎫 Creating Stripe Checkout Session...")
        print(f"   - User: {request.user.email}")
        print(f"   - Price ID: {stripe_price_id}")
        
        session = stripe.checkout.Session.create(
            mode='subscription',
            payment_method_types=['card'],
            line_items=[{
                'price': stripe_price_id,
                'quantity': 1
            }],
            success_url=success_url,
            cancel_url=cancel_url,
            client_reference_id=str(request.user.id),
            metadata={
                'user_id': str(request.user.id),
                'subscription_id': str(subscription.id)
            },
            customer_email=request.user.email if hasattr(request.user, 'email') else None,
        )

        print(f"✅ Checkout Session Created!")
        print(f"   - Session ID: {session.id}")
        print(f"   - Checkout URL: {session.url}")
        print(f"   - Success URL sent to Stripe: {session.success_url}")
        print("=" * 80)

        return Response({
            'success': True,
            'message': 'Checkout session created successfully',
            'checkout_url': session.url,
            'session_id': session.id
        })
    
    except stripe.StripeError as e:
        print(f"❌ STRIPE ERROR: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to create checkout session',
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return Response({
            'success': False,
            'message': 'Internal server error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def verify_payment_public(request):
    """Verify Payment - Public Access (No Authentication Required)"""
    logger.info("🔍 Verifying payment (Public)...")
    session_id = request.query_params.get('session_id')
    logger.info(f"🔑 Raw Session ID from URL: {session_id}")

    if not session_id:
        return Response({
            'success': False,
            'message': 'Session ID is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Clean session ID - remove whitespace, newlines, and URL encoding
        import urllib.parse
        session_id = urllib.parse.unquote(session_id.strip())

        logger.info(
            f"🔑 Cleaned Session ID: '{session_id}', Length: {len(session_id)}")

        # Basic validation - check if session_id is not empty and has reasonable length
        if not session_id or len(session_id) < 10:
            logger.error(f"❌ Session ID too short or empty: '{session_id}'")
            return Response({
                'success': False,
                'message': 'Invalid or missing session ID'
            }, status=status.HTTP_400_BAD_REQUEST)

        # More flexible prefix validation
        # Stripe session IDs typically start with 'cs_' (test or live)
        if not session_id.startswith('cs_'):
            logger.error(
                f"❌ Invalid session ID format: '{session_id[:30]}...'")
            return Response({
                'success': False,
                'message': f'Invalid session ID format. Expected format: cs_xxxxx'
            }, status=status.HTTP_400_BAD_REQUEST)

        logger.info(f"✅ Session ID validation passed, calling Stripe API...")

        # Retrieve checkout session from Stripe
        try:
            session = stripe.checkout.Session.retrieve(session_id)
        except stripe.error.InvalidRequestError as e:
            logger.error(f"❌ Stripe API Error: {str(e)}")
            return Response({
                'success': False,
                'message': f'Invalid session ID: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

        logger.info(f"💰 Stripe Session Status: {session.payment_status}")
        logger.info(
            f"👤 User ID from metadata: {session.metadata.get('user_id')}")
        logger.info(
            f"📦 Subscription ID from metadata: {session.metadata.get('subscription_id')}")

        if session.payment_status != 'paid':
            return Response({
                'success': False,
                'message': f'Payment not completed. Current status: {session.payment_status}'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get subscription and user info
        subscription_id = session.metadata.get('subscription_id')
        user_id = session.metadata.get('user_id')

        if not subscription_id or not user_id:
            logger.error(
                f"❌ Missing metadata - subscription_id: {subscription_id}, user_id: {user_id}")
            return Response({
                'success': False,
                'message': 'Missing user or subscription information in session metadata'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check for duplicate payment
        payment_intent = session.payment_intent
        if payment_intent:
            existing_payment = Payment.objects.filter(
                transaction_id=payment_intent).first()
            if existing_payment:
                logger.info(
                    f"🔄 Payment already exists (ID: {existing_payment.id}), returning existing data")
                return Response({
                    'success': True,
                    'message': 'Payment already verified',
                    'data': PaymentSerializer(existing_payment).data
                })

        try:
            subscription = Subscription.objects.get(id=subscription_id)
        except Subscription.DoesNotExist:
            logger.error(f"❌ Subscription not found: {subscription_id}")
            return Response({
                'success': False,
                'message': 'Subscription plan not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Calculate validity dates
        now = timezone.now()
        if subscription.billing_cycle == 'monthly':
            valid_till = now + relativedelta(months=1)
        else:  # yearly
            valid_till = now + relativedelta(years=1)

        # Safely retrieve invoice ID
        invoice_id = session.invoice if session.invoice else Payment.generate_invoice_id()

        logger.info(f"💾 Creating payment record...")

        # Save payment
        payment = Payment.objects.create(
            user_id=user_id,
            subscription=subscription,
            stripe_subscription_id=session.subscription,
            amount=session.amount_total / 100,  # Convert from cents
            # Fallback to session ID if no payment intent
            transaction_id=payment_intent or session.id,
            invoice_id=invoice_id,
            status='succeeded',
            payment_date=now
        )

        logger.info(
            f"✅ Payment created successfully! Payment ID: {payment.id}")

        # Update or create user subscription
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
        logger.info(f"👤 User subscription {action}: {user_subscription.id}")

        # Send email confirmation
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(id=user_id)
            send_payment_email(
                email=user.email,
                amount=payment.amount,
                transaction_id=payment.transaction_id,
                invoice_id=payment.invoice_id,
                payment_status='succeeded'
            )
            logger.info(f"📧 Email sent to: {user.email}")
        except Exception as email_error:
            logger.warning(f"⚠️ Email sending failed: {str(email_error)}")

        logger.info(f"✅ Payment verification completed successfully!")

        return Response({
            'success': True,
            'message': 'Payment verified successfully',
            'data': PaymentSerializer(payment).data
        })

    except stripe.error.StripeError as e:
        logger.error(f"❌ Stripe API Error: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'message': f'Stripe API error: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"🔴 Unexpected error: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'message': 'Internal server error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def payment_success_page(request):
    """Render payment success page"""
    # Log session_id for debugging
    session_id = request.GET.get('session_id', 'Not provided')
    logger.info(
        f"🎯 Payment success page accessed with session_id: {session_id}")
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
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter payments for non-admin users"""
        if self.request.user.is_staff:
            return Payment.objects.all()
        return Payment.objects.filter(user=self.request.user)


    @action(detail=False, methods=['get'], url_path='total-earnings', permission_classes=[IsAdminUser])
    def total_earnings(self, request):
        """Get Total Earnings"""
        total = Payment.objects.filter(status='succeeded').aggregate(
            total=Sum('amount')
        )['total'] or 0

        return Response({
            'success': True,
            'message': 'Total earnings fetched successfully',
            'data': {'total': float(total)}
        })

    @action(detail=False, methods=['get'], url_path='todays-earnings', permission_classes=[IsAdminUser])
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

    @action(detail=False, methods=['get'], url_path='monthly-stats', permission_classes=[IsAdminUser])
    def monthly_stats(self, request):
        """Get Monthly Earnings Stats with Growth Percentage"""
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

    @action(detail=False, methods=['get'], url_path='earnings-overview', permission_classes=[IsAdminUser])
    def earnings_overview(self, request):
        """Get 12 Months Earnings Overview"""
        year = request.query_params.get('year')

        if year:
            try:
                base_date = datetime(int(year), 12, 31)
            except ValueError:
                return Response({
                    'success': False,
                    'message': 'Invalid year format'
                }, status=status.HTTP_400_BAD_REQUEST)
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
                'year': month_date.year,
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
        """
        user = request.user
        now = timezone.now()

        try:
            # Get the user's active subscription record
            user_subscription = UserSubscription.objects.get(
                user=user,
                status='active'
            )

            # Check if subscription has expired
            if user_subscription.expires_at < now:
                logger.warning(
                    f"⚠️ Subscription {user_subscription.id} has expired. Updating status to 'expired'.")
                user_subscription.status = 'expired'
                user_subscription.save()
                raise UserSubscription.DoesNotExist

            # Get the subscription plan details
            subscription = user_subscription.plan
            plan_data = SubscriptionSerializer(subscription).data

            # Get the Optery UUID from settings
            optery_uuid = getattr(
                settings, 'OPTERY_INTEGRATION_UUID', '8f48c726-728b-49cc-88fe-a8e3425f0594')

            # Construct the final response data
            response_data = {
                'plan': plan_data,
                'starts_at': user_subscription.starts_at,
                'expires_at': user_subscription.expires_at,
                'status': user_subscription.status,
                'plan_uuid': optery_uuid
            }

            return Response({
                'success': True,
                'message': 'Current active subscription fetched successfully',
                'data': response_data
            })

        except UserSubscription.DoesNotExist:
            return Response({
                'success': False,
                'message': 'No active subscription found for this user',
                'data': None
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.error(
                f"Error fetching current subscription for user {user.id}: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': 'Internal server error while fetching subscription',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ======================== WEBHOOK HANDLERS ========================

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def stripe_webhook(request):
    """
    ✅ SECURE STRIPE WEBHOOK
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error(f"Invalid payload: {e}")
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {e}")
        return JsonResponse({'error': 'Invalid signature'}, status=400)

    event_type = event['type']
    data = event['data']['object']

    logger.info(f"📨 Received webhook event: {event_type}")

    # Handle different event types
    if event_type == 'checkout.session.completed':
        handle_checkout_session_completed(data)

    elif event_type == 'invoice.paid':
        handle_invoice_paid(data)

    elif event_type == 'invoice.payment_failed':
        handle_invoice_failed(data)

    elif event_type == 'customer.subscription.deleted':
        handle_subscription_cancelled(data)

    return JsonResponse({'received': True})


def handle_checkout_session_completed(session):
    """Handle completed checkout session"""
    try:
        logger.info(f"🔍 Processing checkout session: {session['id']}")

        # Check if payment is successful
        if session.get('payment_status') != 'paid':
            logger.warning(
                f"⚠️ Payment not completed. Status: {session.get('payment_status')}")
            return

        # Extract metadata
        metadata = session.get('metadata', {})
        subscription_id = metadata.get('subscription_id')
        user_id = metadata.get('user_id')

        logger.info(
            f"📋 Metadata - subscription_id: {subscription_id}, user_id: {user_id}")

        if not subscription_id or not user_id:
            logger.error("❌ Missing required metadata in session")
            return

        # Check if payment already exists to avoid duplicates
        payment_intent = session.get('payment_intent')
        if payment_intent:
            existing_payment = Payment.objects.filter(
                transaction_id=payment_intent).first()
            if existing_payment:
                logger.info(
                    f"✅ Payment already exists in database: {existing_payment.id}")
                return

        # Get subscription
        try:
            subscription = Subscription.objects.get(id=subscription_id)
            logger.info(f"📦 Subscription found: {subscription.title}")
        except Subscription.DoesNotExist:
            logger.error(f"❌ Subscription not found: {subscription_id}")
            return

        # Calculate validity dates
        now = timezone.now()
        if subscription.billing_cycle == 'monthly':
            valid_till = now + relativedelta(months=1)
        else:  # yearly
            valid_till = now + relativedelta(years=1)

        logger.info(f"📅 Validity calculated: {valid_till}")

        # Get invoice ID
        invoice_id = session.get('invoice') or Payment.generate_invoice_id()

        # Create payment record
        try:
            payment = Payment.objects.create(
                user_id=user_id,
                subscription=subscription,
                stripe_subscription_id=session.get('subscription'),
                amount=session.get('amount_total', 0) /
                100,  # Convert from cents
                transaction_id=payment_intent,
                invoice_id=invoice_id,
                status='succeeded',
                payment_date=now
            )
            logger.info(f"💰 Payment created successfully: {payment.id}")
        except Exception as e:
            logger.error(f"❌ Payment creation failed: {e}", exc_info=True)
            return

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
            logger.info(
                f"👤 User subscription {action}: {user_subscription.id}")
        except Exception as e:
            logger.error(
                f"❌ User subscription update failed: {e}", exc_info=True)

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
            logger.info(f"📧 Email sent to: {user.email}")
        except Exception as e:
            logger.warning(f"⚠️ Email sending failed: {e}")

        logger.info("✅ Checkout session processing completed successfully")

    except Exception as e:
        logger.error(
            f"❌ Error in handle_checkout_session_completed: {str(e)}", exc_info=True)


def handle_invoice_paid(invoice):
    """Handle successful invoice payment (for recurring subscriptions)"""
    try:
        logger.info(f"💳 Processing paid invoice: {invoice['id']}")

        subscription_id = invoice.get('subscription')

        if not subscription_id:
            logger.warning("⚠️ No subscription ID in invoice")
            return

        # Find the payment record by stripe subscription ID
        payment = Payment.objects.filter(
            stripe_subscription_id=subscription_id).order_by('-created_at').first()

        if payment:
            # Update user subscription validity
            user_subscription = UserSubscription.objects.filter(
                user_id=payment.user_id).first()

            if user_subscription:
                now = timezone.now()
                if user_subscription.plan.billing_cycle == 'monthly':
                    valid_till = now + relativedelta(months=1)
                else:
                    valid_till = now + relativedelta(years=1)

                user_subscription.expires_at = valid_till
                user_subscription.status = 'active'
                user_subscription.save()

                # Create new payment record for this renewal
                Payment.objects.create(
                    user=payment.user,
                    subscription=payment.subscription,
                    stripe_subscription_id=subscription_id,
                    amount=invoice.get('amount_paid', 0) / 100,
                    transaction_id=invoice.get(
                        'payment_intent', f"pi_{invoice['id']}"),
                    invoice_id=invoice['id'],
                    status='succeeded',
                    payment_date=now
                )

                logger.info(f"✅ Subscription renewed until: {valid_till}")

    except Exception as e:
        logger.error(
            f"❌ Error in handle_invoice_paid: {str(e)}", exc_info=True)


def handle_invoice_failed(invoice):
    """Handle failed invoice payment"""
    try:
        logger.info(f"❌ Processing failed invoice: {invoice['id']}")

        subscription_id = invoice.get('subscription')

        if subscription_id:
            payment = Payment.objects.filter(
                stripe_subscription_id=subscription_id).order_by('-created_at').first()

            if payment:
                # Update user subscription status
                user_subscription = UserSubscription.objects.filter(
                    user_id=payment.user_id).first()

                if user_subscription:
                    user_subscription.status = 'payment_failed'
                    user_subscription.save()

                    logger.info(
                        f"⚠️ Subscription marked as payment failed for user: {payment.user_id}")

    except Exception as e:
        logger.error(
            f"❌ Error in handle_invoice_failed: {str(e)}", exc_info=True)


def handle_subscription_cancelled(subscription):
    """Handle subscription cancellation"""
    try:
        logger.info(
            f"🚫 Processing cancelled subscription: {subscription['id']}")

        stripe_subscription_id = subscription['id']

        # Find payment with this subscription ID
        payment = Payment.objects.filter(
            stripe_subscription_id=stripe_subscription_id).order_by('-created_at').first()

        if payment:
            # Update user subscription status
            user_subscription = UserSubscription.objects.filter(
                user_id=payment.user_id).first()

            if user_subscription:
                user_subscription.status = 'cancelled'
                user_subscription.save()

                logger.info(
                    f"✅ Subscription cancelled for user: {payment.user_id}")

    except Exception as e:
        logger.error(
            f"❌ Error in handle_subscription_cancelled: {str(e)}", exc_info=True)
