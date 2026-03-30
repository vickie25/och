#!/usr/bin/env python3
"""
Test script for mentor credit and rating functionality.
Run with: python3 test_mentor_credits.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.insert(0, '/Users/airm1/Projects/och/backend/django_app')
django.setup()

from django.contrib.auth import get_user_model
from mentors.models import Mentor, MentorRating, MentorCredit, CreditTransaction, CreditRedemption
from mentors.services import MentorCreditService

User = get_user_model()

def test_credit_calculation():
    """Test that credit values are calculated correctly for each star rating."""
    print("\n=== Testing Credit Calculation ===")
    
    test_cases = [
        (5, 10),  # 5 stars = 10 credits
        (4, 8),   # 4 stars = 8 credits
        (3, 6),   # 3 stars = 6 credits
        (2, 4),   # 2 stars = 4 credits
        (1, 2),   # 1 star = 2 credits
    ]
    
    for stars, expected_credits in test_cases:
        rating = MentorRating(rating=stars)
        actual_credits = rating.calculate_credits()
        
        if actual_credits == expected_credits:
            print(f"✓ {stars} stars = {actual_credits} credits (expected: {expected_credits})")
        else:
            print(f"✗ {stars} stars = {actual_credits} credits (expected: {expected_credits}) - FAILED")
            return False
    
    return True

def test_redemption_costs():
    """Test that redemption costs are correct."""
    print("\n=== Testing Redemption Costs ===")
    
    expected_costs = {
        'course': 50,
        'certificate': 30,
        'badge': 20,
        'priority_matching': 40,
        'featured_profile': 100,
    }
    
    for redemption_type, expected_cost in expected_costs.items():
        actual_cost = CreditRedemption.get_cost(redemption_type)
        
        if actual_cost == expected_cost:
            print(f"✓ {redemption_type} = {actual_cost} credits")
        else:
            print(f"✗ {redemption_type} = {actual_cost} credits (expected: {expected_cost}) - FAILED")
            return False
    
    return True

def test_credit_service_methods():
    """Test MentorCreditService methods exist and are callable."""
    print("\n=== Testing Credit Service Methods ===")
    
    methods_to_test = [
        'award_credits_for_rating',
        'redeem_credits',
        'get_credit_summary',
        'get_transaction_history',
        'get_redemption_options',
    ]
    
    for method_name in methods_to_test:
        if hasattr(MentorCreditService, method_name):
            print(f"✓ MentorCreditService.{method_name} exists")
        else:
            print(f"✗ MentorCreditService.{method_name} not found - FAILED")
            return False
    
    return True

def test_model_creation():
    """Test that models can be instantiated."""
    print("\n=== Testing Model Creation ===")
    
    try:
        # Create test user
        test_user, _ = User.objects.get_or_create(
            email='test_credit_user@example.com',
            defaults={
                'first_name': 'Test',
                'last_name': 'User',
            }
        )
        
        # Create mentor
        mentor, _ = Mentor.objects.get_or_create(
            user=test_user,
            defaults={
                'mentor_slug': 'test-mentor-credit',
                'bio': 'Test mentor for credit system',
            }
        )
        print(f"✓ Mentor created: {mentor.mentor_slug}")
        
        # Create student user
        student_user, _ = User.objects.get_or_create(
            email='test_student_credit@example.com',
            defaults={
                'first_name': 'Test',
                'last_name': 'Student',
            }
        )
        
        # Create rating
        rating, created = MentorRating.objects.get_or_create(
            mentor=mentor,
            student=student_user,
            defaults={
                'rating': 5,
                'review': 'Excellent mentor!',
            }
        )
        print(f"✓ Rating {'created' if created else 'updated'}: {rating.rating} stars")
        
        # Check credit balance was created
        try:
            credit_balance = mentor.credit_balance
            print(f"✓ Credit balance exists: {credit_balance.current_balance} credits")
        except MentorCredit.DoesNotExist:
            print("✗ Credit balance not created - FAILED")
            return False
        
        # Check transaction was recorded
        transactions = mentor.credit_transactions.filter(related_rating=rating)
        if transactions.exists():
            print(f"✓ Transaction recorded: {transactions.first().amount} credits")
        else:
            print("✗ Transaction not recorded - FAILED")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error during model creation test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("="*60)
    print("MENTOR CREDIT & RATING SYSTEM TEST")
    print("="*60)
    
    tests = [
        ("Credit Calculation", test_credit_calculation),
        ("Redemption Costs", test_redemption_costs),
        ("Credit Service Methods", test_credit_service_methods),
        ("Model Creation", test_model_creation),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Mentor credit system is working correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the output above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
