from django.db.models import Q
from .models import Message


def unread_messages_count(request):
    """Context processor that returns count of unread messages for the authenticated user.

    Count criteria:
    - Message.read is False
    - Message.conversation includes the current user
    - Message.sender is not the current user
    """
    if not request.user.is_authenticated:
        return {}

    count = Message.objects.filter(
        conversation__participants=request.user,
        read=False
    ).exclude(sender=request.user).count()

    return {'unread_messages_count': count}
