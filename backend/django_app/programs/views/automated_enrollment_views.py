"""
Automated Enrollment Views - No manual review, automated grading.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from datetime import timedelta
from decimal import Decimal
import secrets
import hashlib

from programs.models import CohortPublicApplication, Cohort, Enrollment
from programs.permissions import IsProgramDirector

User = get_user_model()

import logging
logger = logging.getLogger(__name__)


def generate_onboarding_token(application_id):
    """Generate secure token for onboarding link."""
    random_string = secrets.token_urlsafe(32)
    combined = f"{application_id}-{random_string}-{timezone.now().timestamp()}"
    return hashlib.sha256(combined.encode()).hexdigest()


def send_onboarding_email(application):
    """
    Send onboarding email with account creation link (no credentials).
    """
    cohort = application.cohort
    email = application.form_data.get('email')
    name = application.form_data.get('name', 'Student')
    
    # Generate secure token
    token = generate_onboarding_token(application.id)
    application.onboarding_token = token
    application.onboarding_link_sent_at = timezone.now()
    application.save()
    
    # Create onboarding link
    onboarding_link = f"{settings.FRONTEND_URL}/onboarding/create-account?token={token}"
    
    # Payment deadline
    deadline = application.payment_deadline.strftime('%B %d, %Y at %I:%M %p %Z')
    hours_remaining = int((application.payment_deadline - timezone.now()).total_seconds() / 3600)
    
    subject = f"🎉 Welcome to {cohort.name} - Create Your Account"
    
    message = f"""
Dear {name},

Congratulations! You have been accepted into {cohort.name}! 🎓

Your application test score qualified you for enrollment. Now it's time to complete your registration.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

NEXT STEPS:

1️⃣ CREATE YOUR ACCOUNT
   Click the link below to set your password:
   {onboarding_link}
   
   This link is unique to you and expires in 7 days.

2️⃣ COMPLETE PAYMENT
   After creating your account, you'll be directed to the payment page.
   
   ⚠️ IMPORTANT: Payment must be completed within {hours_remaining} hours
   
   Enrollment Fee: ${cohort.enrollment_fee} USD
   Payment Methods: 
   • Credit/Debit Card (Visa, Mastercard)
   • Bank Transfer
   • Mobile Money (M-Pesa, Airtel Money, Orange Money)
   
   Payment Deadline: {deadline}

3️⃣ START LEARNING
   Once payment is verified, you'll:
   • Complete your learning profile
   • Access Foundations module
   • Join your cohort and start learning!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏰ PAYMENT DEADLINE: {deadline}

If you don't complete payment by the deadline, your spot will be released to 
students on the waitlist.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

COHORT DETAILS:
• Cohort: {cohort.name}
• Start Date: {cohort.start_date.strftime('%B %d, %Y')}
• End Date: {cohort.end_date.strftime('%B %d, %Y')}
• Mode: {cohort.get_mode_display()}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Questions? Reply to this email or contact:
📧 support@och.com
🌐 {settings.FRONTEND_URL}/support

Welcome to the OCH community! We're excited to have you on this journey.

Best regards,
The OCH Team

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This is an automated message. Please do not reply directly to this email.
    """
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False
        )
        logger.info(f"Onboarding email sent to {email} for cohort {cohort.name}")
    except Exception as e:
        logger.error(f"Failed to send onboarding email to {email}: {str(e)}")
        raise


def send_rejection_email(application):
    """Send rejection email to failed applicant."""
    cohort = application.cohort
    email = application.form_data.get('email')
    name = application.form_data.get('name', 'Applicant')
    
    subject = f"Application Update - {cohort.name}"
    
    message = f"""
Dear {name},

Thank you for your interest in {cohort.name}.

After careful review of all applications, we regret to inform you that we are 
unable to offer you a spot in this cohort at this time.

We received a high volume of applications and had to make difficult decisions 
based on available capacity and program requirements.

WHAT'S NEXT:

• We encourage you to apply for future cohorts
• Consider strengthening your skills in the meantime
• Check our website for upcoming cohort announcements
• Explore our self-paced learning options

We appreciate your interest in OCH and wish you the best in your cybersecurity 
journey.

Best regards,
The OCH Team

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Questions? Contact us at support@och.com
    """
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False
        )
        logger.info(f"Rejection email sent to {email} for cohort {cohort.name}")
    except Exception as e:
        logger.error(f"Failed to send rejection email to {email}: {str(e)}")


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsProgramDirector])
def auto_grade_applications(request):
    """
    POST /api/v1/programs/director/public-applications/auto-grade/
    
    Automatically grade all applications based on cut-off score.
    
    Request:
    {
        "cohort_id": "uuid",
        "cutoff_score": 70.0,
        "payment_deadline_hours": 48
    }
    
    Response:
    {
        "passed": 25,
        "failed": 15,
        "waitlist": 15,
        "total": 55,
        "emails_sent": 25
    }
    """
    try:
        cohort_id = request.data.get('cohort_id')
        cutoff_score = Decimal(str(request.data.get('cutoff_score', 70)))
        payment_deadline_hours = int(request.data.get('payment_deadline_hours', 48))
        
        if not cohort_id:
            return Response(
                {'error': 'cohort_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get cohort
        try:
            cohort = Cohort.objects.get(id=cohort_id)
        except Cohort.DoesNotExist:
            return Response(
                {'error': 'Cohort not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get all applications with completed tests
        applications = CohortPublicApplication.objects.filter(
            cohort_id=cohort_id,
            status='pending',
            review_status='reviewed'  # Test completed and graded
        )
        
        if not applications.exists():
            return Response(
                {'error': 'No applications ready for grading'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        passed = 0
        failed = 0
        emails_sent = 0
        errors = []
        
        payment_deadline = timezone.now() + timedelta(hours=payment_deadline_hours)
        
        for app in applications:
            try:
                if app.review_score and app.review_score >= cutoff_score:
                    # PASSED - Send onboarding email
                    app.status = 'approved'
                    app.review_status = 'passed'
                    app.payment_deadline = payment_deadline
                    app.save()
                    
                    # Send onboarding email
                    try:
                        send_onboarding_email(app)
                        emails_sent += 1
                    except Exception as e:
                        errors.append(f"Failed to send email to {app.form_data.get('email')}: {str(e)}")
                    
                    passed += 1
                else:
                    # FAILED - Add to waitlist
                    app.review_status = 'failed'
                    app.status = 'pending'  # Keep as pending (waitlist)
                    app.save()
                    failed += 1
            
            except Exception as e:
                errors.append(f"Error processing application {app.id}: {str(e)}")
                logger.error(f"Error processing application {app.id}: {str(e)}")
        
        response_data = {
            'passed': passed,
            'failed': failed,
            'waitlist': failed,
            'total': passed + failed,
            'emails_sent': emails_sent,
            'cutoff_score': float(cutoff_score),
            'payment_deadline_hours': payment_deadline_hours,
            'message': f'Graded {passed + failed} applications. {passed} passed, {failed} on waitlist.'
        }
        
        if errors:
            response_data['errors'] = errors
        
        return Response(response_data)
    
    except Exception as e:
        logger.error(f"Auto-grade error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsProgramDirector])
def send_rejection_emails(request):
    """
    POST /api/v1/programs/director/public-applications/send-rejections/
    
    Send rejection emails to waitlisted students.
    
    Request:
    {
        "cohort_id": "uuid",
        "application_ids": ["uuid1", "uuid2", ...]  # Optional
    }
    
    Response:
    {
        "rejected": 15,
        "emails_sent": 15,
        "errors": []
    }
    """
    try:
        cohort_id = request.data.get('cohort_id')
        application_ids = request.data.get('application_ids', [])
        
        if not cohort_id:
            return Response(
                {'error': 'cohort_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get waitlisted applications
        query = CohortPublicApplication.objects.filter(
            cohort_id=cohort_id,
            review_status='failed',
            status='pending'
        )
        
        if application_ids:
            query = query.filter(id__in=application_ids)
        
        rejected_count = 0
        emails_sent = 0
        errors = []
        
        for app in query:
            try:
                # Update status
                app.status = 'rejected'
                app.save()
                rejected_count += 1
                
                # Send rejection email
                try:
                    send_rejection_email(app)
                    emails_sent += 1
                except Exception as e:
                    errors.append(f"Failed to send email to {app.form_data.get('email')}: {str(e)}")
            
            except Exception as e:
                errors.append(f"Error processing application {app.id}: {str(e)}")
                logger.error(f"Error processing application {app.id}: {str(e)}")
        
        response_data = {
            'rejected': rejected_count,
            'emails_sent': emails_sent,
            'message': f'Sent {emails_sent} rejection emails to {rejected_count} applicants'
        }
        
        if errors:
            response_data['errors'] = errors
        
        return Response(response_data)
    
    except Exception as e:
        logger.error(f"Send rejections error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def verify_onboarding_token(request):
    """
    GET /api/v1/programs/onboarding/verify-token?token=xxx
    
    Verify onboarding token and return application data.
    
    Response:
    {
        "valid": true,
        "email": "student@example.com",
        "name": "John Doe",
        "cohort_name": "Cybersecurity Bootcamp 2024",
        "cohort_id": "uuid",
        "application_id": "uuid",
        "payment_deadline": "2024-01-15T12:00:00Z"
    }
    """
    try:
        token = request.query_params.get('token')
        
        if not token:
            return Response(
                {'error': 'token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find application by token
        try:
            application = CohortPublicApplication.objects.select_related('cohort').get(
                onboarding_token=token,
                status='approved'
            )
        except CohortPublicApplication.DoesNotExist:
            return Response(
                {'error': 'Invalid or expired token'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if token expired (7 days)
        if application.onboarding_link_sent_at:
            token_age = timezone.now() - application.onboarding_link_sent_at
            if token_age.days > 7:
                return Response(
                    {'error': 'Token has expired. Please contact support.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Check if payment deadline passed
        if application.payment_deadline and application.payment_deadline < timezone.now():
            application.status = 'rejected'
            application.save()
            return Response(
                {'error': 'Payment deadline has passed. Your spot has been released.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'valid': True,
            'email': application.form_data.get('email'),
            'name': application.form_data.get('name', 'Student'),
            'cohort_name': application.cohort.name,
            'cohort_id': str(application.cohort.id),
            'application_id': str(application.id),
            'payment_deadline': application.payment_deadline.isoformat() if application.payment_deadline else None,
            'enrollment_fee': float(application.cohort.enrollment_fee) if hasattr(application.cohort, 'enrollment_fee') else 100.00
        })
    
    except Exception as e:
        logger.error(f"Verify token error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def create_account_from_token(request):
    """
    POST /api/v1/programs/onboarding/create-account
    
    Create user account from onboarding token.
    
    Request:
    {
        "token": "xxx",
        "password": "securepassword123"
    }
    
    Response:
    {
        "user_id": "uuid",
        "enrollment_id": "uuid",
        "email": "student@example.com",
        "message": "Account created successfully"
    }
    """
    try:
        token = request.data.get('token')
        password = request.data.get('password')
        
        if not token or not password:
            return Response(
                {'error': 'token and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate password
        if len(password) < 8:
            return Response(
                {'error': 'Password must be at least 8 characters'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find application
        try:
            application = CohortPublicApplication.objects.select_related('cohort').get(
                onboarding_token=token,
                status='approved'
            )
        except CohortPublicApplication.DoesNotExist:
            return Response(
                {'error': 'Invalid or expired token'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if payment deadline passed
        if application.payment_deadline and application.payment_deadline < timezone.now():
            application.status = 'rejected'
            application.save()
            return Response(
                {'error': 'Payment deadline has passed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user already exists
        email = application.form_data.get('email')
        if User.objects.filter(email=email).exists():
            return Response(
                {'error': 'An account with this email already exists. Please login.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create user
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=application.form_data.get('first_name', ''),
            last_name=application.form_data.get('last_name', ''),
            is_active=True,
            account_status='active'
        )
        
        # Create enrollment
        enrollment = Enrollment.objects.create(
            cohort=application.cohort,
            user=user,
            enrollment_type='self',
            seat_type='paid',
            payment_status='pending',
            status='pending_payment'
        )
        
        # Link application to enrollment
        application.enrollment = enrollment
        application.password_created_at = timezone.now()
        application.save()
        
        logger.info(f"Account created for {email}, enrollment {enrollment.id}")
        
        return Response({
            'user_id': str(user.id),
            'enrollment_id': str(enrollment.id),
            'email': email,
            'cohort_id': str(application.cohort.id),
            'payment_deadline': application.payment_deadline.isoformat() if application.payment_deadline else None,
            'message': 'Account created successfully. Please complete payment.'
        }, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        logger.error(f"Create account error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsProgramDirector])
def get_waitlist(request):
    """
    GET /api/v1/programs/director/public-applications/waitlist?cohort_id=uuid
    
    Get waitlisted applications.
    
    Response:
    {
        "waitlist": [
            {
                "id": "uuid",
                "name": "John Doe",
                "email": "john@example.com",
                "review_score": 65.5,
                "applied_at": "2024-01-01T00:00:00Z"
            }
        ],
        "count": 15
    }
    """
    try:
        cohort_id = request.query_params.get('cohort_id')
        
        if not cohort_id:
            return Response(
                {'error': 'cohort_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get waitlisted applications
        applications = CohortPublicApplication.objects.filter(
            cohort_id=cohort_id,
            review_status='failed',
            status='pending'
        ).order_by('-review_score', 'created_at')
        
        waitlist_data = []
        for app in applications:
            waitlist_data.append({
                'id': str(app.id),
                'name': app.form_data.get('name', 'Unknown'),
                'email': app.form_data.get('email'),
                'review_score': float(app.review_score) if app.review_score else 0,
                'applied_at': app.created_at.isoformat(),
                'form_data': app.form_data
            })
        
        return Response({
            'waitlist': waitlist_data,
            'count': len(waitlist_data)
        })
    
    except Exception as e:
        logger.error(f"Get waitlist error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
