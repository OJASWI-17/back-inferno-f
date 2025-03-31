# mainapp/middleware.py
from django.contrib.auth import logout

class SessionAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip for ASGI requests without user attribute
        if not hasattr(request, 'user'):
            return self.get_response(request)
            
        if request.user.is_authenticated and not request.session.session_key:
            logout(request)
        return self.get_response(request)