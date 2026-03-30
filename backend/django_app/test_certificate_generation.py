#!/usr/bin/env python3
"""
Certificate Generation Test Suite
Tests eligibility checks, generation, and validation.
Run with: python3 test_certificate_generation.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.insert(0, '/Users/airm1/Projects/och/backend/django_app')
django.setup()

from datetime import datetime, timedelta
from django.utils import timezone
from programs.services.certificate_eligibility_service import CertificateEligibilityService
from programs.services.certificate_docx_generator import CertificateDOCXGenerator


def test_eligibility_service():
    """Test the eligibility service with various scenarios."""
    print("\n" + "="*60)
    print("CERTIFICATE ELIGIBILITY SERVICE TESTS")
    print("="*60)
    
    # Test 1: Check enrollment completion
    print("\n[Test 1] Checking enrollment completion logic...")
    try:
        from programs.models import Enrollment
        
        # Find a completed enrollment to test with
        completed_enrollment = Enrollment.objects.filter(status='completed').first()
        
        if completed_enrollment:
            is_eligible, details = CertificateEligibilityService.check_eligibility(completed_enrollment)
            
            print(f"  Enrollment ID: {completed_enrollment.id}")
            print(f"  Status: {completed_enrollment.status}")
            print(f"  Completed At: {completed_enrollment.completed_at}")
            print(f"  Is Eligible: {is_eligible}")
            print(f"  Summary: {details['summary']}")
            
            # Display all checks
            for check_name, check_data in details['checks'].items():
                status_icon = "✓" if check_data['passed'] else "✗"
                print(f"    {status_icon} {check_data['name']}: {check_data['message']}")
            
            return True
        else:
            print("  ⚠ No completed enrollments found for testing")
            return None
            
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_template_mapping():
    """Test track/level to template mapping."""
    print("\n" + "="*60)
    print("TEMPLATE MAPPING TESTS")
    print("="*60)
    
    test_cases = [
        ('DEF', 'Beginner', False, 'OCH_Certificate_DEF_Beginner'),
        ('DEF', 'Intermediate', False, 'OCH_Certificate_DEF_Intermediate'),
        ('DEF', 'Advanced', False, 'OCH_Certificate_DEF_Advanced'),
        ('DEF', 'Mastery', False, 'OCH_Certificate_DEF_Mastery'),
        ('INN', 'Beginner', False, 'OCH_Certificate_INN_Beginner'),
        ('GRC', 'Advanced', False, 'OCH_Certificate_GRC_Advanced'),
        ('OFF', 'Mastery', False, 'OCH_Certificate_OFF_Mastery'),
        ('L0', 'Beginner', False, 'OCH_Certificate_L0_Beginner'),
        (None, None, True, 'OCH_Certificate_Cohort'),  # Cohort template
    ]
    
    all_passed = True
    for track_key, level, is_cohort, expected in test_cases:
        result = CertificateDOCXGenerator.get_template_for_track_level(track_key, level, is_cohort)
        passed = result == expected
        status = "✓" if passed else "✗"
        print(f"  {status} {track_key or 'COHORT'}/{level or 'N/A'} -> {result}")
        if not passed:
            print(f"     Expected: {expected}")
            all_passed = False
    
    return all_passed


def test_placeholder_extraction():
    """Test extracting placeholders from templates."""
    print("\n" + "="*60)
    print("PLACEHOLDER EXTRACTION TESTS")
    print("="*60)
    
    templates = CertificateDOCXGenerator.list_available_templates()
    print(f"  Found {len(templates)} templates: {templates}")
    
    if templates:
        # Check placeholders in first template
        template = templates[0]
        placeholders = CertificateDOCXGenerator.get_template_placeholders(template)
        print(f"\n  Template: {template}")
        print(f"  Placeholders found: {len(placeholders)}")
        for ph in placeholders[:10]:  # Show first 10
            print(f"    - {{{{{ph}}}}}")
        if len(placeholders) > 10:
            print(f"    ... and {len(placeholders) - 10} more")
        return True
    else:
        print("  ⚠ No templates found")
        return None


def test_docx_generation():
    """Test actual DOCX certificate generation."""
    print("\n" + "="*60)
    print("DOCX GENERATION TEST")
    print("="*60)
    
    try:
        from programs.models import Certificate
        
        # Find a certificate to test with
        certificate = Certificate.objects.first()
        
        if not certificate:
            print("  ⚠ No certificates found for testing")
            return None
        
        print(f"  Testing with certificate: {certificate.id}")
        print(f"  Track: {certificate.enrollment.cohort.track.name}")
        print(f"  Student: {certificate.enrollment.user.email}")
        
        # Try to generate DOCX
        try:
            docx_bytes = CertificateDOCXGenerator.generate_certificate_docx(certificate)
            size_kb = len(docx_bytes) / 1024
            print(f"  ✓ Generated DOCX successfully")
            print(f"  ✓ File size: {size_kb:.2f} KB")
            
            # Save to test file
            test_path = '/tmp/test_certificate.docx'
            with open(test_path, 'wb') as f:
                f.write(docx_bytes)
            print(f"  ✓ Saved to: {test_path}")
            
            return True
            
        except Exception as e:
            print(f"  ✗ Generation failed: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"  ✗ Test setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all certificate tests."""
    print("\n" + "="*60)
    print("CERTIFICATE GENERATION TEST SUITE")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("Eligibility Service", test_eligibility_service()))
    results.append(("Template Mapping", test_template_mapping()))
    results.append(("Placeholder Extraction", test_placeholder_extraction()))
    results.append(("DOCX Generation", test_docx_generation()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = 0
    failed = 0
    skipped = 0
    
    for test_name, result in results:
        if result is True:
            status = "✓ PASSED"
            passed += 1
        elif result is False:
            status = "✗ FAILED"
            failed += 1
        else:
            status = "⚠ SKIPPED"
            skipped += 1
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed} passed, {failed} failed, {skipped} skipped")
    
    if failed == 0:
        print("\n🎉 All tests completed successfully!")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the output above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
