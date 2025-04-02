# mainapp/middleware.py
from django.contrib.auth import logout
import logging

logger = logging.getLogger(__name__)

class SessionAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.exempt_urls = ['/healthcheck/', '/status/']

    def __call__(self, request):
        # Skip middleware for certain paths and ASGI requests
        if (not hasattr(request, 'user') or 
            any(request.path.startswith(url) for url in self.exempt_urls)):
            return self.get_response(request)
            
        # Handle session verification
        if request.user.is_authenticated:
            session_key = request.session.session_key
            if not session_key or not request.session.exists(session_key):
                logger.warning(
                    f"Invalid session for user {request.user.id} - IP: {request.META.get('REMOTE_ADDR')}"
                )
                logout(request)
                
        return self.get_response(request)