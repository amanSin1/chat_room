# chat/models.py
from django.db import models
from django.contrib.auth import get_user_model

# Get the active user model (usually django.contrib.auth.models.User)
User = get_user_model()

class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp'] # Order messages by time, oldest first

    def __str__(self):
        return f"{self.user.username}: {self.content[:50]}" # Display first 50 chars of content
    
class Notification(models.Model):
    # The user who *receives* the notification
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp'] # Newest notifications first
        # Add a unique_together constraint if you want to prevent duplicate notifications
        # for the same user with the same message at the same time.
        # unique_together = ('recipient', 'message', 'timestamp')

    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.message[:50]} (Read: {self.is_read})"