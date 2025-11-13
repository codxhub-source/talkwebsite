from django import template
from django.utils import timezone

register = template.Library()

@register.filter
def online_status(user):
    """Return the user's online status as a Bootstrap class"""
    if not user.last_activity:
        return 'text-danger'  # offline
        
    now = timezone.now()
    delta = now - user.last_activity
    
    if delta.total_seconds() < 300:  # 5 minutes
        return 'text-success'  # online
    elif delta.total_seconds() < 900:  # 15 minutes
        return 'text-warning'  # away
    else:
        return 'text-danger'  # offline