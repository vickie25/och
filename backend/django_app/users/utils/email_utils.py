"""
Email utilities for sending magic links, OTP codes, and verification emails.
"""
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


def send_magic_link_email(user, code, magic_link_url):
    """
    Send magic link email to user.

    Args:
        user: User instance
        code: Magic link code
        magic_link_url: Full URL with code (e.g., https://app.example.com/auth/verify?code=xxx)
    """
    subject = 'Sign in to Ongoza CyberHub'

    html_message = render_to_string('emails/magic_link.html', {
        'user': user,
        'magic_link_url': magic_link_url,
        'code': code,
    })

    plain_message = strip_tags(html_message)

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send magic link email to {user.email}: {str(e)}")
        # Backup log for emergencies
        print(f"BACKUP ACCESS CODE LOG: {user.email} -> {code}")
        return False


def send_otp_email(user, code):
    """
    Send OTP code via email.

    Args:
        user: User instance
        code: OTP code (6-digit)
    """
    subject = 'Your Ongoza CyberHub verification code'

    html_message = render_to_string('emails/otp_code.html', {
        'user': user,
        'code': code,
    })

    plain_message = f'Your verification code is: {code}\n\nThis code will expire in 10 minutes.'

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send OTP email to {user.email}: {str(e)}")
        # Backup log for emergencies
        print(f"BACKUP OTP LOG: {user.email} -> {code}")
        return False


def send_verification_email(user, verification_url):
    """
    Send email verification link via EmailService (Django SMTP / console backend).

    Args:
        user: User instance
        verification_url: Full verification URL with code and email
    """
    try:
        # Extract code from URL if present
        import urllib.parse

        from services.email_service import email_service
        parsed_url = urllib.parse.urlparse(verification_url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        # query_params.get('code', [None])[0] # Unused but preserved logic

        # Create HTML content for verification email
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                @media (prefers-color-scheme: dark) {{
                    .body-wrapper {{ background-color: #0F172A !important; }}
                    .card {{ background-color: #1E293B !important; color: #F1F5F9 !important; }}
                }}
            </style>
        </head>
        <body style="margin: 0; padding: 0; background-color: #F8FAFC; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; padding: 40px 20px;">
                <div style="text-align: center; margin-bottom: 24px;">
                    <span style="font-weight: 800; font-size: 24px; color: #1E3A8A; letter-spacing: -0.5px;">ONGOZA <span style="color: #F97316;">CYBERHUB</span></span>
                </div>

                <div style="background-color: #FFFFFF; border-radius: 12px; padding: 40px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); border-top: 4px solid #1E3A8A;">
                    <h2 style="margin-top: 0; color: #1E3A8A; font-size: 20px; font-weight: 700;">Verify Your Email</h2>
                    <div style="color: #334155; line-height: 1.6; font-size: 16px;">
                        <p>Hi {user.first_name or 'Explorer'},</p>
                        <p>Thank you for signing up! Please verify your email address by clicking the button below:</p>

                        <div style="text-align: center; margin-top: 32px;">
                            <a href="{verification_url}" style="background-color: #1E3A8A; color: #ffffff; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: 600; display: inline-block; font-size: 16px;">
                                Verify Email Address
                            </a>
                        </div>

                        <p style="background: #F8FAFC; padding: 12px; border-radius: 6px; font-size: 14px; color: #475569; margin-top: 24px;">
                            <strong>Security Note:</strong> This verification link will expire in 60 minutes. If you didn't create an account, please ignore this email.
                        </p>
                    </div>
                </div>

                <div style="text-align: center; margin-top: 24px;">
                    <p style="color: #64748B; font-size: 13px;">
                        © {getattr(settings, 'CURRENT_YEAR', '2026')} Ongoza CyberHub | Mission-Driven Education<br>
                        Bank Row, Cloud Park, OT Valley Districts
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        return email_service._execute_send(
            user.email,
            "Verify your Ongoza CyberHub email",
            html_content,
            "verification"
        )
    except Exception as e:
        logger.error(f"Failed to send verification email via EmailService: {str(e)}")
        # Fallback to Django's send_mail
        try:
            subject = 'Verify your Ongoza CyberHub email'
            html_message = render_to_string('emails/verify_email.html', {
                'user': user,
                'verification_url': verification_url,
            })
            plain_message = strip_tags(html_message)
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            return True
        except Exception as e2:
            logger.error(f"Fallback verification email also failed for {user.email}: {str(e2)}")
            return False


def send_onboarding_email(user):
    """
    Send student onboarding email that drives users into the self-onboarding flow.
    """
    import secrets
    from services.email_service import email_service
    from users.utils.auth_utils import create_mfa_code

    # Generate tracking token and persist on user.metadata
    try:
        tracking_token = secrets.token_urlsafe(32)
        if not getattr(user, "metadata", None):
            user.metadata = {}
        user.metadata["onboarding_email_token"] = tracking_token
        user.save(update_fields=["metadata"])
    except Exception as e:
        logger.warning(f"Failed to set onboarding_email_token for {user.email}: {str(e)}")
        tracking_token = None

    # Build tracking pixel URL (backend API)
    backend_url = getattr(settings, "DJANGO_API_URL", "http://localhost:8000")
    if not backend_url:
        backend_url = getattr(settings, "API_URL", "http://localhost:8000")
    tracking_url = None
    if tracking_token:
        tracking_url = f"{backend_url}/api/v1/track-onboarding-email?token={tracking_token}&user_id={user.id}"

    # Frontend URL for onboarding flow
    frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")

    onboarding_url = None
    try:
        code, _ = create_mfa_code(user, method="magic_link", expires_minutes=1440)  # 24h
        onboarding_url = (
            f"{frontend_url.rstrip('/')}/auth/setup-password"
            f"?code={code}&email={user.email}&redirect=/onboarding/ai-profiler"
        )
    except Exception as e:
        logger.warning(
            f"Failed to generate magic-link code for onboarding email to {user.email}: {str(e)}"
        )
        # Fallback: direct link using only email param
        onboarding_url = (
            f"{frontend_url.rstrip('/')}/auth/setup-password"
            f"?email={user.email}&redirect=/onboarding/ai-profiler"
        )

    # Final fallback
    if not onboarding_url:
        onboarding_url = f"{frontend_url.rstrip('/')}/onboarding/student?email={user.email}"

    tracking_pixel = (
        f'<img src="{tracking_url}" width="1" height="1" style="display:none;" alt="" />'
        if tracking_url
        else ""
    )

    # Simplified HTML for rewrite
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <body style="margin: 0; padding: 0; background-color: #F8FAFC; font-family: sans-serif;">
        <div style="max-width: 600px; margin: 0 auto; padding: 40px 20px;">
            <div style="text-align: center; margin-bottom: 24px;">
                <span style="font-weight: 800; font-size: 24px; color: #1E3A8A;">
                    ONGOZA <span style="color: #F97316;">CYBERHUB</span>
                </span>
            </div>
            <div style="background-color: #FFFFFF; border-radius: 12px; padding: 40px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-top: 4px solid #1E3A8A;">
                <h2 style="color: #1E3A8A; font-size: 20px;">Welcome to Ongoza CyberHub!</h2>
                <p>Hi {user.first_name or 'Explorer'},</p>
                <p>Welcome! Click the button below to begin your onboarding:</p>
                <div style="text-align: center; margin-top: 32px;">
                    <a href="{onboarding_url}" style="background-color: #1E3A8A; color: #ffffff; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: 600; display: inline-block;">
                        Get Started
                    </a>
                </div>
            </div>
            {tracking_pixel}
        </div>
    </body>
    </html>
    """

    try:
        success = email_service._execute_send(
            user.email,
            "Welcome to Ongoza CyberHub - Get Started Today!",
            html_content,
            "onboarding",
        )
        if success:
            try:
                user.onboarded_email_status = "sent"
                user.save(update_fields=["onboarded_email_status"])
            except Exception as e:
                logger.warning(f"Failed to update onboarded_email_status for {user.email}: {str(e)}")
        return success
    except Exception as e:
        logger.error(f"Error while sending onboarding email to {user.email}: {str(e)}")
        return False


def send_password_reset_email(user, reset_url):
    """
    Send password reset link.
    """
    subject = 'Reset your Ongoza CyberHub password'

    html_message = render_to_string('emails/password_reset.html', {
        'user': user,
        'reset_url': reset_url,
    })

    plain_message = strip_tags(html_message)

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {str(e)}")
        return False


def send_application_credentials_email(user, cohort_name, reset_url, applicant_type='student'):
  """
  Send an acceptance + credentials email for a cohort application.
  """
  if applicant_type == 'sponsor':
      subject = f'Your Sponsor Access for {cohort_name}'
  else:
      subject = f'You are enrolled in {cohort_name}'

  html_message = render_to_string('emails/application_credentials.html', {
      'user': user,
      'cohort_name': cohort_name,
      'reset_url': reset_url,
      'applicant_type': applicant_type,
  })

  plain_message = strip_tags(html_message)

  try:
      send_mail(
          subject=subject,
          message=plain_message,
          from_email=settings.DEFAULT_FROM_EMAIL,
          recipient_list=[user.email],
          html_message=html_message,
          fail_silently=False,
      )
      return True
  except Exception as e:
      logger.error(f"Failed to send application credentials email to {user.email}: {str(e)}")
      return False


def send_application_test_email(to_email: str, cohort_name: str, applicant_name: str = '', assessment_url: str = ''):
    """
    Send application test invite email to an applicant.
    """
    subject = f'Congratulations – Your next step with {cohort_name}'
    html_message = render_to_string('emails/application_test_invite.html', {
        'applicant_name': applicant_name or 'there',
        'cohort_name': cohort_name,
        'assessment_url': assessment_url or '#',
    })
    plain_message = strip_tags(html_message)
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send application test email to {to_email}: {str(e)}")
        return False


def send_mfa_enrollment_email(user, method):
    """
    Send MFA enrollment confirmation email.
    """
    subject = 'MFA enabled on your Ongoza CyberHub account'

    html_message = render_to_string('emails/mfa_enabled.html', {
        'user': user,
        'method': method,
    })

    plain_message = f'MFA has been enabled on your account using {method}.'

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send MFA enabled email to {user.email}: {str(e)}")
        return False
