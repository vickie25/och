"""
Certificate Service - Certificate generation and issuance triggers.
"""
import logging
from typing import Any

from django.db import transaction
from django.utils import timezone

from programs.core_services import auto_graduate_cohort
from programs.models import Certificate, Cohort, Enrollment
from programs.services.certificate_eligibility_service import CertificateEligibilityService

logger = logging.getLogger(__name__)


class CertificateService:
    """Service for certificate management."""

    @staticmethod
    @transaction.atomic
    def issue_certificate(enrollment: Enrollment, auto_approve: bool = False) -> Certificate:
        """
        Issue certificate for a completed enrollment.

        Args:
            enrollment: Enrollment instance
            auto_approve: If True, automatically approve without manual review

        Returns:
            Certificate instance
        """
        if enrollment.status != 'completed':
            raise ValueError(f"Enrollment {enrollment.id} is not completed")

        # Enforce eligibility gates: completion, no pending payments, missions complete, etc.
        is_eligible, details = CertificateEligibilityService.check_eligibility(enrollment)
        if not is_eligible:
            raise ValueError(f"Enrollment {enrollment.id} not eligible for certificate: {details.get('summary')}")

        # Check if certificate already exists
        existing = Certificate.objects.filter(enrollment=enrollment).first()
        if existing:
            return existing

        issue_date = timezone.now().date()
        from datetime import timedelta
        expiry_date = issue_date + timedelta(days=365)

        certificate = Certificate.objects.create(
            enrollment=enrollment,
            issue_date=issue_date,
            expiry_date=expiry_date,
            status='active',
            file_uri='',
        )

        # Attempt to generate a DOCX and persist via storage (same path as director generation).
        try:
            from programs.services.certificate_docx_generator import (
                DOCX_AVAILABLE,
                CertificateDOCXGenerator,
            )
            if DOCX_AVAILABLE:
                docx_content = CertificateDOCXGenerator.generate_certificate_docx(certificate)
                from django.core.files.base import ContentFile
                filename = f"certificate_{certificate.id}.docx"
                from django.core.files.storage import default_storage
                path = default_storage.save(f"certificates/generated/{filename}", ContentFile(docx_content))
                certificate.file_uri = default_storage.url(path)
                certificate.save(update_fields=["file_uri"])
        except Exception as e:
            logger.warning("Certificate DOCX generation skipped for %s: %s", certificate.id, e)

        logger.info(f"Issued certificate {certificate.id} for enrollment {enrollment.id}")
        return certificate

    @staticmethod
    @transaction.atomic
    def trigger_cohort_certificates(cohort: Cohort, auto_approve: bool = False) -> dict[str, Any]:
        """
        Trigger certificate issuance for all completed enrollments in a cohort.

        Args:
            cohort: Cohort instance
            auto_approve: If True, automatically approve all certificates

        Returns:
            Dict with issuance statistics
        """
        # First, auto-graduate eligible students
        graduation_result = auto_graduate_cohort(cohort.id)

        # Issue certificates for completed enrollments
        completed_enrollments = Enrollment.objects.filter(
            cohort=cohort,
            status='completed'
        )

        issued_count = 0
        skipped_count = 0
        errors = []

        for enrollment in completed_enrollments:
            try:
                # Check if certificate already exists
                if hasattr(enrollment, 'certificate'):
                    skipped_count += 1
                    continue

                CertificateService.issue_certificate(enrollment, auto_approve)
                issued_count += 1
            except Exception as e:
                errors.append(f"Error issuing certificate for enrollment {enrollment.id}: {str(e)}")
                logger.error(f"Certificate issuance error: {e}")

        result = {
            'cohort_id': str(cohort.id),
            'graduated': graduation_result.get('completed', 0),
            'certificates_issued': issued_count,
            'certificates_skipped': skipped_count,
            'errors': errors,
        }

        logger.info(f"Certificate trigger completed for cohort {cohort.id}: {result}")
        return result

    @staticmethod
    @transaction.atomic
    def archive_cohort_and_issue_certificates(cohort: Cohort) -> dict[str, Any]:
        """
        Archive a cohort and trigger certificate issuance.
        This is called when cohort status changes to 'closed'.

        Args:
            cohort: Cohort instance

        Returns:
            Dict with archive and certificate statistics
        """
        if cohort.status != 'closing':
            raise ValueError(f"Cohort {cohort.id} must be in 'closing' status before archiving")

        # Trigger certificate issuance
        certificate_result = CertificateService.trigger_cohort_certificates(cohort, auto_approve=True)

        # Update cohort status to closed
        cohort.status = 'closed'
        cohort.save()

        # TODO: Trigger analytics pipeline
        # TODO: Generate final reports
        # TODO: Notify stakeholders

        result = {
            'cohort_id': str(cohort.id),
            'status': 'closed',
            'certificates': certificate_result,
            'archived_at': timezone.now().isoformat(),
        }

        logger.info(f"Cohort {cohort.id} archived: {result}")
        return result

