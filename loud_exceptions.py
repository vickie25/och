import logging
import traceback
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    
    if response is None:
        # RETURN THE RAW TRACEBACK FOR EMERGENCY DEBUGGING
        return Response(
            {
                'detail': str(exc),
                'exception_class': exc.__class__.__name__,
                'traceback': traceback.format_exc()
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # Also inject the traceback into existing DRF responses for visibility
    if isinstance(response.data, dict):
        response.data['traceback'] = traceback.format_exc()
        
    return response

def safe_error_response(message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
    return Response({'detail': message}, status=status_code)
