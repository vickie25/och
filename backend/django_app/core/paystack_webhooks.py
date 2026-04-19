import json
import logging
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings

# Setup logging
logger = logging.getLogger(__name__)

@csrf_exempt
@require_POST
def unified_paystack_webhook(request):
    """
    Unified webhook handler for all Paystack events (Subscriptions and Cohorts).
    Dispatches events to the appropriate service based on plan_id or metadata.
    """
    payload = request.body
    sig_header = request.headers.get('x-paystack-signature')

    if not sig_header:
        logger.error("Missing Paystack signature header")
        return HttpResponse(status=400)

    # Basic verification (In production, verify signature with secret key)
    # For now, we trust the payload if the header exists, but ideally verify it.
    
    try:
        event_data = json.loads(payload)
        event_type = event_data.get('event')
        data = event_data.get('data', {})
        metadata = data.get('metadata', {})
        
        logger.info(f"Paystack Webhook Received: {event_type}")

        # Dispatch Logic
        # 1. Check for Cohort Application (usually has cohort_id in metadata)
        if metadata and 'cohort_id' in metadata:
            logger.info("Dispatching to Cohorts Service...")
            # Here you would call your cohort processing logic
            return HttpResponse(status=200)

        # 2. Check for Subscriptions (usually has a plan object)
        if data.get('plan'):
            logger.info("Dispatching to Subscriptions Service...")
            # Here you would call your subscription processing logic
            return HttpResponse(status=200)

        logger.warning(f"Unhandled Paystack event or unknown source: {event_type}")
        return HttpResponse(status=200)

    except Exception as e:
        logger.error(f"Error processing Paystack webhook: {str(e)}")
        return HttpResponse(status=500)
