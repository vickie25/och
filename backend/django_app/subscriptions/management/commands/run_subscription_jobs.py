from django.core.management.base import BaseCommand

from subscriptions.scheduler import (
    process_auto_renewals,
    process_grace_period_downgrades,
    process_payment_retries,
    send_payment_reminders,
)


class Command(BaseCommand):
    help = 'Run subscription management jobs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--job',
            type=str,
            choices=['renewals', 'retries', 'grace', 'reminders', 'all'],
            default='all',
            help='Specify which job to run'
        )

    def handle(self, *args, **options):
        job = options['job']

        if job in ['renewals', 'all']:
            self.stdout.write('Processing auto-renewals...')
            process_auto_renewals()
            self.stdout.write(self.style.SUCCESS('Auto-renewals processed'))

        if job in ['retries', 'all']:
            self.stdout.write('Processing payment retries...')
            process_payment_retries()
            self.stdout.write(self.style.SUCCESS('Payment retries processed'))

        if job in ['grace', 'all']:
            self.stdout.write('Processing grace period downgrades...')
            process_grace_period_downgrades()
            self.stdout.write(self.style.SUCCESS('Grace period downgrades processed'))

        if job in ['reminders', 'all']:
            self.stdout.write('Sending payment reminders...')
            send_payment_reminders()
            self.stdout.write(self.style.SUCCESS('Payment reminders sent'))

        self.stdout.write(self.style.SUCCESS('All jobs completed successfully'))
