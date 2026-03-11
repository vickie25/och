"""
Paystack Payment Service for Cohort Enrollment.
"""
import requests
import secrets
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from cohorts.models import CohortPayment
from programs.models import Enrollment


class PaystackService:
    """Service for handling Paystack payments."""
    
    BASE_URL = "https://api.paystack.co"
    
    def __init__(self):
        self.secret_key = getattr(settings, 'PAYSTACK_SECRET_KEY', '')
        self.public_key = getattr(settings, 'PAYSTACK_PUBLIC_KEY', '')
        self.headers = {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json',
        }
    
    def generate_reference(self):
        """Generate unique payment reference."""
        return f"OCH-{secrets.token_urlsafe(16)}"
    
    def initialize_payment(self, enrollment, amount, currency='USD', callback_url=None):
        """
        Initialize payment for cohort enrollment.
        
        Args:
            enrollment: Enrollment instance
            amount: Payment amount
            currency: Currency code (default: USD)
            callback_url: URL to redirect after payment
        
        Returns:
            CohortPayment instance with authorization URL
        """
        # Convert amount to kobo/cents (Paystack uses smallest currency unit)
        amount_in_kobo = int(Decimal(amount) * 100)
        
        # Generate reference
        reference = self.generate_reference()
        
        # Create payment record
        payment = CohortPayment.objects.create(
            enrollment=enrollment,
            amount=amount,
            currency=currency,
            paystack_reference=reference,
            status='pending'
        )
        
        # Prepare payload
        payload = {
            'email': enrollment.user.email,
            'amount': amount_in_kobo,
            'currency': currency,
            'reference': reference,
            'callback_url': callback_url or f"{settings.FRONTEND_URL}/dashboard/student/cohorts/payment/verify",
            'metadata': {
                'enrollment_id': str(enrollment.id),
                'cohort_id': str(enrollment.cohort.id),
                'cohort_name': enrollment.cohort.name,
                'user_id': str(enrollment.user.id),
                'user_email': enrollment.user.email,
            }
        }
        
        try:
            # Make API request
            response = requests.post(
                f"{self.BASE_URL}/transaction/initialize",
                json=payload,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status'):
                # Update payment with Paystack response
                payment.paystack_access_code = data['data'].get('access_code', '')
                payment.paystack_authorization_url = data['data'].get('authorization_url', '')
                payment.paystack_response = data
                payment.status = 'processing'
                payment.save()
                
                return payment
            else:
                payment.status = 'failed'
                payment.paystack_response = data
                payment.save()
                raise Exception(f"Paystack initialization failed: {data.get('message')}")
        
        except requests.exceptions.RequestException as e:
            payment.status = 'failed'
            payment.paystack_response = {'error': str(e)}
            payment.save()
            raise Exception(f"Payment initialization failed: {str(e)}")
    
    def verify_payment(self, reference):
        """
        Verify payment with Paystack.
        
        Args:
            reference: Payment reference
        
        Returns:
            CohortPayment instance with updated status
        """
        try:
            payment = CohortPayment.objects.get(paystack_reference=reference)
        except CohortPayment.DoesNotExist:
            raise Exception(f"Payment with reference {reference} not found")
        
        try:
            # Verify with Paystack
            response = requests.get(
                f"{self.BASE_URL}/transaction/verify/{reference}",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') and data['data'].get('status') == 'success':
                # Payment successful
                payment.status = 'completed'
                payment.completed_at = timezone.now()
                payment.verified_at = timezone.now()
                payment.paystack_response = data
                payment.save()
                
                # Update enrollment status
                enrollment = payment.enrollment
                enrollment.payment_status = 'paid'
                enrollment.status = 'active'
                enrollment.save()
                
                return payment
            else:
                # Payment failed
                payment.status = 'failed'
                payment.paystack_response = data
                payment.save()
                raise Exception(f"Payment verification failed: {data.get('message')}")
        
        except requests.exceptions.RequestException as e:
            payment.status = 'failed'
            payment.paystack_response = {'error': str(e)}
            payment.save()
            raise Exception(f"Payment verification failed: {str(e)}")
    
    def get_payment_status(self, reference):
        """
        Get payment status.
        
        Args:
            reference: Payment reference
        
        Returns:
            dict with payment status
        """
        try:
            payment = CohortPayment.objects.get(paystack_reference=reference)
            return {
                'status': payment.status,
                'amount': float(payment.amount),
                'currency': payment.currency,
                'reference': payment.paystack_reference,
                'completed_at': payment.completed_at.isoformat() if payment.completed_at else None,
            }
        except CohortPayment.DoesNotExist:
            return {'status': 'not_found'}
    
    def refund_payment(self, reference, amount=None):
        """
        Refund payment (if supported by Paystack).
        
        Args:
            reference: Payment reference
            amount: Amount to refund (optional, defaults to full amount)
        
        Returns:
            dict with refund status
        """
        try:
            payment = CohortPayment.objects.get(paystack_reference=reference)
        except CohortPayment.DoesNotExist:
            raise Exception(f"Payment with reference {reference} not found")
        
        if payment.status != 'completed':
            raise Exception("Can only refund completed payments")
        
        # Paystack refund endpoint
        refund_amount = amount or payment.amount
        refund_amount_in_kobo = int(Decimal(refund_amount) * 100)
        
        payload = {
            'transaction': reference,
            'amount': refund_amount_in_kobo,
        }
        
        try:
            response = requests.post(
                f"{self.BASE_URL}/refund",
                json=payload,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status'):
                payment.status = 'refunded'
                payment.paystack_response = data
                payment.save()
                
                # Update enrollment
                enrollment = payment.enrollment
                enrollment.payment_status = 'pending'
                enrollment.status = 'withdrawn'
                enrollment.save()
                
                return {'status': 'success', 'message': 'Refund processed'}
            else:
                raise Exception(f"Refund failed: {data.get('message')}")
        
        except requests.exceptions.RequestException as e:
            raise Exception(f"Refund failed: {str(e)}")


# Singleton instance
paystack_service = PaystackService()
