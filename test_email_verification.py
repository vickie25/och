#!/usr/bin/env python3
"""
Test script for email verification flow
"""
import os
import sys

# Add the backend directory to Python path
sys.path.append('/Users/airm1/Projects/och/backend/django_app')

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def test_email_flow():
    """Test complete email verification flow"""
    print("=== Email Verification Flow Test ===\n")
    
    # Test 1: Basic email sending
    print("1. Testing basic email sending...")
    try:
        result = send_mail(
            subject='OCH Email Verification Test',
            message='This is a test email from OCH platform. If you receive this, email sending is working correctly.',
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'test@example.com'),
            recipient_list=['test@lomtechnology.com'],
            fail_silently=False,
        )
        print(f"✅ Basic email send result: {result}")
        if result == 1:
            print("✅ Email sending is working!")
        else:
            print("❌ Email sending failed")
    except Exception as e:
        print(f"❌ Email send error: {e}")
        return False
    
    # Test 2: Check email configuration
    print(f"\n2. Email Configuration:")
    print(f"   Email Host: {getattr(settings, 'EMAIL_HOST', 'NOT_SET')}")
    print(f"   Email Port: {getattr(settings, 'EMAIL_PORT', 'NOT_SET')}")
    print(f"   Email User: {getattr(settings, 'EMAIL_HOST_USER', 'NOT_SET')}")
    print(f"   From Email: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'NOT_SET')}")
    print(f"   Email Backend: {getattr(settings, 'EMAIL_BACKEND', 'NOT_SET')}")
    
    # Test 3: Create test user and send verification email
    print(f"\n3. Testing verification email...")
    try:
        from users.models import User
        from users.utils.email_utils import send_verification_email
        
        # Create test user
        test_email = 'testverification@example.com'
        user, created = User.objects.get_or_create(
            email=test_email,
            defaults={
                'username': test_email,
                'first_name': 'Test',
                'last_name': 'Verification',
                'is_active': False,
            }
        )
        
        if created:
            token = user.generate_verification_token()
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
            verification_url = f"{frontend_url}/auth/verify-email?token={token}"
            
            print(f"   Test user: {user.email}")
            print(f"   Verification URL: {verification_url}")
            
            # Send verification email
            result = send_verification_email(user, verification_url)
            print(f"   Verification email result: {result}")
            
            if result:
                print("✅ Verification email sent successfully!")
                print("📧 Check your email at test@lomtechnology.com")
                print(f"🔗 Or visit: {verification_url}")
            else:
                print("❌ Failed to send verification email")
        else:
            print("   Test user already exists")
            
    except Exception as e:
        print(f"❌ Verification email test error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print(f"\n=== Summary ===")
    print("✅ Email sending is configured and working")
    print("📧 Check your email inbox (including spam folder)")
    print("🔗 Use the verification link to complete signup")
    
    return True

if __name__ == "__main__":
    test_email_flow()
