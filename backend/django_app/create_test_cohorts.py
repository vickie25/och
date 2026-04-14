"""
Create Test Cohorts for Browsing
Run this script to add sample cohorts to the database.
"""
import os
import sys
from datetime import date, timedelta

import django

# Add the Django project to the Python path
sys.path.append('/path/to/och/backend/django_app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from programs.models import Cohort, Program, Track

User = get_user_model()

def create_test_cohorts():
    """Create test cohorts for browsing."""

    # Get or create a test program
    program, created = Program.objects.get_or_create(
        name='Cybersecurity Professional Program',
        defaults={
            'category': 'technical',
            'description': 'Comprehensive cybersecurity training program',
            'duration_months': 6,
            'default_price': 100.00
        }
    )

    # Get or create test tracks
    defender_track, created = Track.objects.get_or_create(
        program=program,
        key='defender',
        defaults={
            'name': 'Cyber Defense',
            'description': 'Learn defensive cybersecurity techniques'
        }
    )

    offensive_track, created = Track.objects.get_or_create(
        program=program,
        key='offensive',
        defaults={
            'name': 'Offensive Security',
            'description': 'Learn ethical hacking and penetration testing'
        }
    )

    grc_track, created = Track.objects.get_or_create(
        program=program,
        key='grc',
        defaults={
            'name': 'Governance, Risk & Compliance',
            'description': 'Learn cybersecurity governance and compliance'
        }
    )

    # Create test cohorts
    cohorts_data = [
        {
            'name': 'Cyber Defense Bootcamp - Spring 2024',
            'track': defender_track,
            'start_date': date.today() + timedelta(days=30),
            'end_date': date.today() + timedelta(days=120),
            'mode': 'virtual',
            'seat_cap': 50,
            'enrollment_fee': 150.00,
        },
        {
            'name': 'Ethical Hacking Intensive - Q2 2024',
            'track': offensive_track,
            'start_date': date.today() + timedelta(days=45),
            'end_date': date.today() + timedelta(days=135),
            'mode': 'hybrid',
            'seat_cap': 30,
            'enrollment_fee': 200.00,
        },
        {
            'name': 'GRC Fundamentals - Summer 2024',
            'track': grc_track,
            'start_date': date.today() + timedelta(days=60),
            'end_date': date.today() + timedelta(days=150),
            'mode': 'onsite',
            'seat_cap': 25,
            'enrollment_fee': 175.00,
        },
        {
            'name': 'Advanced Cyber Defense - Fall 2024',
            'track': defender_track,
            'start_date': date.today() + timedelta(days=90),
            'end_date': date.today() + timedelta(days=180),
            'mode': 'virtual',
            'seat_cap': 40,
            'enrollment_fee': 250.00,
        }
    ]

    created_count = 0
    for cohort_data in cohorts_data:
        cohort, created = Cohort.objects.get_or_create(
            name=cohort_data['name'],
            defaults={
                **cohort_data,
                'published_to_homepage': True,  # Make visible on browse page
                'status': 'active',
                'mentor_ratio': 0.1,
            }
        )
        if created:
            created_count += 1
            print(f"Created cohort: {cohort.name}")
        else:
            print(f"Cohort already exists: {cohort.name}")

    print(f"\nCreated {created_count} new cohorts")
    print(f"Total published cohorts: {Cohort.objects.filter(published_to_homepage=True).count()}")

if __name__ == '__main__':
    create_test_cohorts()
