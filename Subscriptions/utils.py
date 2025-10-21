from django.core.mail import send_mail
from django.conf import settings


def send_payment_email(email, amount, transaction_id, invoice_id, payment_status):
    """Send payment confirmation email"""
    subject = 'Payment Successful'
    html_message = f"""
    <h2>Payment Confirmation</h2>
    <p>Thank you for your payment of <strong>${amount}</strong>.</p>
    <p>Transaction ID: {transaction_id}</p>
    <p>Invoice ID: {invoice_id}</p>
    <p>Status: {payment_status}</p>
    <p>Thank you for your subscription!</p>
    """
    
    try:
        send_mail(
            subject=subject,
            message='',  # Plain text version
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Email sending failed: {e}")


def calculate_subscription_validity(billing_cycle, start_date=None):
    """Calculate subscription expiry date"""
    from datetime import datetime
    from dateutil.relativedelta import relativedelta
    
    if start_date is None:
        start_date = datetime.now()
    
    if billing_cycle == 'monthly':
        return start_date + relativedelta(months=1)
    elif billing_cycle == 'yearly':
        return start_date + relativedelta(years=1)
    
    return start_date