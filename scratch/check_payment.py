import os
import django
import sys

# Set up Django environment
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

from subscriptions.models import PaymentTransaction as SubPayment
from cohort.models import PaymentTransaction as CohortPayment

def check_payment():
    ref = 'OCH-MO5ITVDJ'
    print(f"Checking for Payment Reference: {ref}")
    
    # Check Subscriptions payment
    try:
        sub_p = SubPayment.objects.get(paystack_reference=ref)
        print(f"Found in SUB: User={sub_p.user.email}, Status={sub_p.status}, Amount={sub_p.amount}")
    except SubPayment.DoesNotExist:
        print("Not found in Subscriptions")
    except Exception as e:
        print(f"Error checking Subscriptions: {e}")

    # Check Cohort payment
    try:
        coh_p = CohortPayment.objects.get(paystack_reference=ref)
        print(f"Found in COHORT: Enrollment={coh_p.enrollment.id}, Status={coh_p.status}, Amount={coh_p.amount}")
    except CohortPayment.DoesNotExist:
        print("Not found in Cohorts")
    except Exception as e:
        print(f"Error checking Cohorts: {e}")

if __name__ == "__main__":
    check_payment()
