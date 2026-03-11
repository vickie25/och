"""
Payment Views - Handle cohort enrollment payments.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from programs.models import Enrollment
from cohorts.models import CohortPayment
from cohorts.services.payment_service import paystack_service
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_cohort_payment(request):
    """
    POST /api/v1/cohorts/payment/initiate
    
    Initiate payment for cohort enrollment.
    
    Request body:
    {
        "enrollment_id": "uuid",
        "callback_url": "optional_url"
    }
    
    Response:
    {
        "payment_id": "uuid",
        "reference": "OCH-xxx",
        "authorization_url": "https://checkout.paystack.com/xxx",
        "amount": 100.00,
        "currency": "USD"
    }
    """
    try:
        enrollment_id = request.data.get('enrollment_id')
        callback_url = request.data.get('callback_url')
        
        if not enrollment_id:
            return Response(
                {'error': 'enrollment_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get enrollment
        try:
            enrollment = Enrollment.objects.get(id=enrollment_id, user=request.user)
        except Enrollment.DoesNotExist:
            return Response(
                {'error': 'Enrollment not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if already paid
        if enrollment.payment_status == 'paid':
            return Response(
                {'error': 'Enrollment already paid'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if payment already exists
        existing_payment = CohortPayment.objects.filter(
            enrollment=enrollment,
            status__in=['pending', 'processing']
        ).first()
        
        if existing_payment:
            return Response({
                'payment_id': str(existing_payment.id),
                'reference': existing_payment.paystack_reference,
                'authorization_url': existing_payment.paystack_authorization_url,
                'amount': float(existing_payment.amount),
                'currency': existing_payment.currency,
                'status': existing_payment.status
            })
        
        # Get cohort price (you can customize this based on your pricing logic)
        cohort = enrollment.cohort
        amount = getattr(cohort, 'enrollment_fee', 100.00)  # Default $100
        
        # Initialize payment
        payment = paystack_service.initialize_payment(
            enrollment=enrollment,
            amount=amount,
            currency='USD',
            callback_url=callback_url
        )
        
        return Response({
            'payment_id': str(payment.id),
            'reference': payment.paystack_reference,
            'authorization_url': payment.paystack_authorization_url,
            'amount': float(payment.amount),
            'currency': payment.currency,
            'status': payment.status
        })
    
    except Exception as e:
        logger.error(f"Payment initiation error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verify_cohort_payment(request):
    """
    GET /api/v1/cohorts/payment/verify?reference=OCH-xxx
    
    Verify payment status.
    
    Response:
    {
        "status": "completed",
        "payment_id": "uuid",
        "enrollment_id": "uuid",
        "amount": 100.00,
        "verified_at": "2024-01-01T00:00:00Z"
    }
    """
    try:
        reference = request.query_params.get('reference')
        
        if not reference:
            return Response(
                {'error': 'reference is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify payment
        payment = paystack_service.verify_payment(reference)
        
        return Response({
            'status': payment.status,
            'payment_id': str(payment.id),
            'enrollment_id': str(payment.enrollment.id),
            'amount': float(payment.amount),
            'currency': payment.currency,
            'verified_at': payment.verified_at.isoformat() if payment.verified_at else None,
            'enrollment_status': payment.enrollment.status,
            'payment_status': payment.enrollment.payment_status
        })
    
    except Exception as e:
        logger.error(f"Payment verification error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def paystack_webhook(request):
    """
    POST /api/v1/cohorts/payment/webhook
    
    Handle Paystack webhook events.
    """
    try:
        # Verify webhook signature
        signature = request.headers.get('x-paystack-signature')
        
        if not signature:
            return Response(
                {'error': 'No signature'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify signature (implement proper verification)
        # For now, we'll process the event
        
        event = request.data
        event_type = event.get('event')
        
        if event_type == 'charge.success':
            # Payment successful
            data = event.get('data', {})
            reference = data.get('reference')
            
            if reference:
                try:
                    payment = paystack_service.verify_payment(reference)
                    logger.info(f"Webhook: Payment {reference} verified successfully")
                except Exception as e:
                    logger.error(f"Webhook: Payment verification failed: {str(e)}")
        
        return Response({'status': 'success'})
    
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_payment_status(request):
    """
    GET /api/v1/cohorts/payment/status?enrollment_id=uuid
    
    Get payment status for enrollment.
    
    Response:
    {
        "has_payment": true,
        "status": "completed",
        "amount": 100.00,
        "reference": "OCH-xxx"
    }
    """
    try:
        enrollment_id = request.query_params.get('enrollment_id')
        
        if not enrollment_id:
            return Response(
                {'error': 'enrollment_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get enrollment
        try:
            enrollment = Enrollment.objects.get(id=enrollment_id, user=request.user)
        except Enrollment.DoesNotExist:
            return Response(
                {'error': 'Enrollment not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get payment
        payment = CohortPayment.objects.filter(enrollment=enrollment).first()
        
        if not payment:
            return Response({
                'has_payment': False,
                'enrollment_status': enrollment.status,
                'payment_status': enrollment.payment_status
            })
        
        return Response({
            'has_payment': True,
            'status': payment.status,
            'amount': float(payment.amount),
            'currency': payment.currency,
            'reference': payment.paystack_reference,
            'initiated_at': payment.initiated_at.isoformat(),
            'completed_at': payment.completed_at.isoformat() if payment.completed_at else None,
            'enrollment_status': enrollment.status,
            'payment_status': enrollment.payment_status
        })
    
    except Exception as e:
        logger.error(f"Get payment status error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
