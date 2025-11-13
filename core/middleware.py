from django.utils import timezone
from django.conf import settings


class UserActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Update last activity timestamp and online status
            request.user.last_activity = timezone.now()
            request.user.is_online = True
            request.user.save(update_fields=['last_activity', 'is_online'])
        
        response = self.get_response(request)
        return response