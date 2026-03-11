"""
Institutional Billing Scheduler - Automated billing processing for institutional contracts.
Handles scheduled billing, overdue processing, and contract renewals.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from organizations.institutional_models import (
    InstitutionalContract,
    InstitutionalBilling,
    InstitutionalBillingSchedule
)
from organizations.institutional_service import InstitutionalBillingService
import logging

logger = logging.getLogger(__name__)


def process_institutional_billing():
    """
    Main function to process all institutional billing tasks.
    Should be run daily via cron job.
    """
    results = {
        'scheduled_billing_processed': 0,
        'overdue_invoices_processed': 0,
        'renewal_notices_sent': 0,
        'errors': []
    }
    
    try:
        # 1. Process scheduled billing
        logger.info("Processing scheduled institutional billing...")
        billing_results = process_scheduled_institutional_billing()
        results['scheduled_billing_processed'] = billing_results['processed']
        results['errors'].extend(billing_results.get('errors', []))
        
        # 2. Process overdue invoices
        logger.info("Processing overdue institutional invoices...")
        overdue_results = InstitutionalBillingService.process_overdue_invoices()
        results['overdue_invoices_processed'] = overdue_results['processed']
        results['errors'].extend(overdue_results.get('errors', []))
        
        # 3. Send contract renewal notices
        logger.info("Processing contract renewal notices...")
        renewal_results = process_contract_renewals()
        results['renewal_notices_sent'] = renewal_results['notices_sent']
        results['errors'].extend(renewal_results.get('errors', []))
        
        logger.info(f"Institutional billing processing completed: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Error in institutional billing processing: {str(e)}")
        results['errors'].append(f"General error: {str(e)}")
        return results


def process_scheduled_institutional_billing():
    """
    Process all scheduled billing that's due today or overdue.
    """
    results = {
        'processed': 0,
        'invoices_generated': [],
        'errors': []
    }
    
    try:
        # Get all pending schedules that are due
        pending_schedules = InstitutionalBillingSchedule.objects.filter(
            is_processed=False,
            next_billing_date__lte=date.today()
        ).select_related('contract__organization')
        
        logger.info(f"Found {pending_schedules.count()} pending billing schedules")
        
        for schedule in pending_schedules:
            try:
                # Skip if contract is not active
                if schedule.contract.status != 'active':
                    logger.warning(f"Skipping schedule {schedule.id} - contract {schedule.contract.contract_number} not active")
                    continue
                
                # Process the billing
                invoice = InstitutionalBillingService.process_scheduled_billing(schedule.id)
                
                # Send invoice email
                email_sent = InstitutionalBillingService.send_invoice_email(invoice.id)
                
                results['processed'] += 1
                results['invoices_generated'].append({
                    'invoice_number': invoice.invoice_number,
                    'contract_number': invoice.contract.contract_number,
                    'organization': invoice.contract.organization.name,
                    'amount': float(invoice.total_amount),
                    'email_sent': email_sent
                })
                
                logger.info(f"Processed billing for contract {schedule.contract.contract_number}, generated invoice {invoice.invoice_number}")
                
            except Exception as e:
                error_msg = f"Error processing schedule {schedule.id}: {str(e)}"
                results['errors'].append(error_msg)
                logger.error(error_msg)
                
                # Update schedule with error
                schedule.processing_attempts += 1
                schedule.last_error = str(e)
                schedule.save()
        
        return results
        
    except Exception as e:
        logger.error(f"Error in scheduled billing processing: {str(e)}")
        results['errors'].append(f"Scheduled billing error: {str(e)}")
        return results


def process_contract_renewals():
    """
    Process contract renewals and send renewal notices.
    """
    results = {
        'notices_sent': 0,
        'contracts_processed': [],
        'errors': []
    }
    
    try:
        # Find contracts that need renewal notices (60 days before expiry)
        renewal_date_threshold = date.today() + timedelta(days=60)
        
        contracts_needing_renewal = InstitutionalContract.objects.filter(
            status='active',
            auto_renew=True,
            end_date__lte=renewal_date_threshold,
            end_date__gt=date.today()
        ).select_related('organization')
        
        logger.info(f"Found {contracts_needing_renewal.count()} contracts needing renewal notices")
        
        for contract in contracts_needing_renewal:
            try:
                # Generate renewal quote
                quote = InstitutionalBillingService.generate_contract_renewal_quote(contract.id)
                
                # Send renewal notice email
                notice_sent = send_contract_renewal_notice(contract, quote)
                
                if notice_sent:
                    results['notices_sent'] += 1
                    results['contracts_processed'].append({
                        'contract_number': contract.contract_number,
                        'organization': contract.organization.name,
                        'expiry_date': contract.end_date.isoformat(),
                        'days_until_expiry': (contract.end_date - date.today()).days
                    })
                
                logger.info(f"Processed renewal for contract {contract.contract_number}")
                
            except Exception as e:
                error_msg = f"Error processing renewal for contract {contract.contract_number}: {str(e)}"
                results['errors'].append(error_msg)
                logger.error(error_msg)
        
        return results
        
    except Exception as e:
        logger.error(f"Error in contract renewal processing: {str(e)}")
        results['errors'].append(f"Renewal processing error: {str(e)}")
        return results


def send_contract_renewal_notice(contract, quote):
    """
    Send contract renewal notice email.
    """
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        
        subject = f"Contract Renewal Notice - {contract.contract_number}"
        
        text_content = f"""
Contract Renewal Notice

Dear {contract.billing_contact_name},

Your institutional contract {contract.contract_number} with OCH is set to expire on {contract.end_date.strftime('%B %d, %Y')}.

Current Contract Details:
- Licensed Seats: {contract.student_seat_count}
- Monthly Rate: ${contract.per_student_rate}/student
- Billing Cycle: {contract.billing_cycle}

To ensure uninterrupted service for your students, please contact our institutional team at institutional@och.com

Best regards,
The OCH Team
        """
        
        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[contract.billing_contact_email],
            fail_silently=False
        )
        
        logger.info(f"Renewal notice sent to {contract.billing_contact_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send renewal notice for contract {contract.contract_number}: {str(e)}")
        return False


class Command(BaseCommand):
    help = 'Process institutional billing tasks'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--task',
            type=str,
            choices=['all', 'billing', 'overdue', 'renewals'],
            default='all',
            help='Specify which task to run'
        )
    
    def handle(self, *args, **options):
        task = options['task']
        
        if task in ['all', 'billing']:
            self.stdout.write('Processing scheduled billing...')
            results = process_scheduled_institutional_billing()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Processed {results["processed"]} billing schedules, '
                    f'generated {len(results["invoices_generated"])} invoices'
                )
            )
            if results['errors']:
                self.stdout.write(self.style.ERROR(f'Errors: {len(results["errors"])}'))
        
        if task in ['all', 'overdue']:
            self.stdout.write('Processing overdue invoices...')
            results = InstitutionalBillingService.process_overdue_invoices()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Processed {results["processed"]} overdue invoices, '
                    f'sent {results["reminders_sent"]} reminders'
                )
            )
        
        if task in ['all', 'renewals']:
            self.stdout.write('Processing contract renewals...')
            results = process_contract_renewals()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Sent {results["notices_sent"]} renewal notices'
                )
            )
        
        if task == 'all':
            self.stdout.write('Running complete institutional billing process...')
            results = process_institutional_billing()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Complete! Processed {results["scheduled_billing_processed"]} billings, '
                    f'{results["overdue_invoices_processed"]} overdue invoices, '
                    f'{results["renewal_notices_sent"]} renewal notices'
                )
            )
            if results['errors']:
                self.stdout.write(
                    self.style.ERROR(f'Total errors: {len(results["errors"])}')
                )
        
        self.stdout.write(self.style.SUCCESS('Institutional billing processing completed!'))