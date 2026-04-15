import logging

from django.core.management.base import BaseCommand

from marketplace.employer_contract_services import EmployerMatchingQueueService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Process employer matching priority queue (Stream C)."

    def handle(self, *args, **options):
        res = EmployerMatchingQueueService.process_next(batch_size=25)
        logger.info(f"Employer matching queue processed: {res}")
        self.stdout.write(self.style.SUCCESS(f"Processed {res.get('processed', 0)} items"))

