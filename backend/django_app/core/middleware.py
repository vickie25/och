"""
Security middleware for login rate limiting and other security features
"""

import time
import logging
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

logger = logging.getLogger(__name__)

class LoginRateLimitMiddleware(MiddlewareMixin):
    """
    Rate limiting middleware for login attempts
    - Max 5 failed attempts per IP per hour
    - Returns 429 after threshold
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
        
    def process_request(self, request):
        # Only apply to login endpoints
        if request.path in ['/api/v1/auth/login', '/api/v1/auth/token/']:
            return self._check_rate_limit(request)
        return None
    
    def _check_rate_limit(self, request):
        # Get client IP
        ip_address = self._get_client_ip(request)
        
        # Cache key for this IP
        cache_key = f"login_attempts:{ip_address}"
        
        # Get current attempts
        attempts = cache.get(cache_key, 0)
        
        # Check if rate limit exceeded
        if attempts >= 5:
            logger.warning(f"Rate limit exceeded for IP: {ip_address}")
            return JsonResponse({
                'error': 'Too many failed login attempts',
                'detail': 'Please try again later',
                'retry_after': 3600  # 1 hour
            }, status=429)
        
        # If this is a POST request (login attempt), increment counter
        if request.method == 'POST':
            # Check if it's a failed attempt (we'll know after processing)
            # We'll increment in process_response if login fails
            request._login_rate_limit_key = cache_key
            
        return None
    
    def process_response(self, request, response):
        # Check if this was a failed login attempt
        if hasattr(request, '_login_rate_limit_key'):
            if request.path in ['/api/v1/auth/login', '/api/v1/auth/token/']:
                if response.status_code in [401, 403]:
                    # Failed login - increment counter
                    cache_key = request._login_rate_limit_key
                    attempts = cache.get(cache_key, 0)
                    cache.set(cache_key, attempts + 1, 3600)  # 1 hour expiry
                elif response.status_code == 200:
                    # Successful login - reset counter
                    cache.delete(request._login_rate_limit_key)
        
        return response
    
    def _get_client_ip(self, request):
        """
        Get client IP address considering proxies
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Add additional security headers to all responses
    """
    
    def process_response(self, request, response):
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Only in production
        if not settings.DEBUG:
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        return response
