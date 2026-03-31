"""
Custom exception handler for Django REST Framework
Provides clean, production-safe error responses
"""

import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from django.core.exceptions import PermissionDenied, ValidationError
import traceback

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns clean error messages in production
    and detailed error information in development.
    """
    # Call DRF's default exception handler first
    response = exception_handler(exc, context)

    if response is None:
        # Handle Django exceptions that DRF doesn't catch
        if isinstance(exc, Http404):
            return Response(
                {'detail': 'The requested resource was not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        elif isinstance(exc, PermissionDenied):
            return Response(
                {'detail': 'You do not have permission to perform this action.'},
                status=status.HTTP_403_FORBIDDEN
            )
        elif isinstance(exc, ValidationError):
            return Response(
                {'detail': str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )
        else:
            # Unknown exception
            logger.error(f"Unhandled exception: {exc}", exc_info=True)
            return Response(
                {'detail': 'Something went wrong.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # Enhance DRF's error responses
    if isinstance(exc, ValidationError):
        # Validation errors should be detailed but clean
        if hasattr(response.data, 'items'):
            # Format validation errors nicely
            formatted_errors = {}
            for field, errors in response.data.items():
                if isinstance(errors, list):
                    formatted_errors[field] = errors
                else:
                    formatted_errors[field] = [str(errors)]
            response.data = {'detail': formatted_errors}
    
    # In production, remove sensitive information
    import os
    is_production = os.environ.get('DJANGO_SETTINGS_MODULE', '').endswith('production')
    
    if is_production:
        # Remove stack traces and internal paths
        if isinstance(response.data, dict):
            # Keep only safe error information
            safe_data = {}
            
            # Preserve standard DRF error structure
            if 'detail' in response.data:
                safe_data['detail'] = response.data['detail']
            
            # Preserve field validation errors
            for key, value in response.data.items():
                if key != 'detail' and not key.startswith('_'):
                    safe_data[key] = value
            
            response.data = safe_data
            
            # Ensure we never expose stack traces
            if 'stacktrace' in response.data:
                del response.data['stacktrace']
            if 'traceback' in response.data:
                del response.data['traceback']
    
    # Log the error for debugging
    logger.error(
        f"API Error: {exc.__class__.__name__}: {str(exc)}",
        extra={
            'status_code': response.status_code,
            'view': context.get('view', {}).__class__.__name__,
            'request_method': context.get('request', {}).method,
            'request_path': context.get('request', {}).path,
        }
    )

    return response


def safe_error_response(message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
    """
    Helper function to create safe error responses
    """
    return Response({'detail': message}, status=status_code)
