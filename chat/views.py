# chat/views.py
from django.shortcuts import render
# chat/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Notification
import datetime # For timestamp
def chat_room(request):
    # What & Why: Pass the current user's ID to the template context
    # We'll pass None if the user is not authenticated (anonymous)
    context = {
        'user_id': request.user.id if request.user.is_authenticated else None,
    }
    return render(request, 'chat/room.html', context) # <-- Pass the context here

# --- NEW: Notification Trigger View ---
def trigger_notification(request, user_id):
    # What & Why: This view simulates an event (like a follow) that triggers a notification.
    # It's an HTTP view, so we use sync_to_async to interact with the async channel layer.

    User = get_user_model()
    recipient_user = get_object_or_404(User, id=user_id)
    message_content = f"Hello {recipient_user.username}! This is a test notification."

    # 1. Save the notification to the database (for persistence)
    notification = Notification.objects.create(
        recipient=recipient_user,
        message=message_content,
        is_read=False # New notifications are unread by default
    )

    # 2. Send the notification via the Channel Layer (for real-time delivery)
    channel_layer = get_channel_layer()
    notification_group_name = f'user_notifications_{recipient_user.id}'

    try:
        async_to_sync(channel_layer.group_send)(
            notification_group_name,
            {
                'type': 'send_notification', # This maps to the method in NotificationConsumer
                'id': notification.id, # Pass the notification ID
                'message': notification.message,
                'timestamp': notification.timestamp.isoformat(), # Pass timestamp
            }
        )
        status_message = f"Notification sent successfully to {recipient_user.username}."
        print(status_message)
        return JsonResponse({"status": "success", "message": status_message}, status=200)
    except Exception as e:
        error_message = f"Error sending notification to {recipient_user.username}: {e}"
        print(error_message)
        return JsonResponse({"status": "error", "message": error_message}, status=500)