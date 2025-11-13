from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils import timezone


class User(AbstractUser):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
    )

    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    age = models.PositiveSmallIntegerField(null=True, blank=True)
    photo = models.ImageField(upload_to='user_photos/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    last_activity = models.DateTimeField(default=timezone.now)
    is_online = models.BooleanField(default=False)
    # Users this user has blocked (they won't be able to message or see each other depending on business rules)
    blocked_users = models.ManyToManyField('self', symmetrical=False, related_name='blocked_by', blank=True)

    def is_adult(self):
        """Check if the user is 18 or older"""
        return (self.age or 0) >= 18

    def opposite_gender(self):
        """Return the opposite gender for search"""
        return 'F' if self.gender == 'M' else 'M'

    def update_last_activity(self):
        """Update user's last activity timestamp and online status"""
        self.last_activity = timezone.now()
        self.is_online = True
        self.save(update_fields=['last_activity', 'is_online'])

    def get_online_status(self):
        """
        Get user's online status.
        Returns a tuple of (status, duration) where status is either 'online', 'away', or 'offline'
        """
        if not self.last_activity:
            return 'offline', None
        
        now = timezone.now()
        delta = now - self.last_activity
        
        if delta.total_seconds() < 300:  # 5 minutes
            return 'online', None
        elif delta.total_seconds() < 900:  # 15 minutes
            return 'away', delta
        else:
            self.is_online = False
            self.save(update_fields=['is_online'])
            return 'offline', delta

    def __str__(self):
        return f"{self.username} ({self.get_gender_display()})"


class Conversation(models.Model):
    """A simple conversation between two or more users."""
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')
    created_at = models.DateTimeField(default=timezone.now)
    typing_users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='typing_in_conversations', blank=True)

    def __str__(self):
        return f"Conversation {self.pk} ({', '.join(p.username for p in self.participants.all())})"

    def other_participant(self, user):
        return self.participants.exclude(pk=user.pk).first()

    def get_typing_users(self, exclude_user=None):
        """Get users who are currently typing, optionally excluding a specific user"""
        qs = self.typing_users.all()
        if exclude_user:
            qs = qs.exclude(pk=exclude_user.pk)
        return qs


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_messages', on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    read = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"Message {self.pk} from {self.sender.username} at {self.timestamp}"







