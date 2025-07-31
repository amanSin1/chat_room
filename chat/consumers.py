# chat/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async # <-- Import this for database operations
from .models import ChatMessage, Notification # <-- Import your new model and Notification

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = 'public_chat_room'
        self.room_group_name = 'chat_%s' % self.room_name

        if self.scope["user"].is_anonymous:
            print(f"WebSocket connection rejected: User is anonymous.")
            await self.close()
            return

        print(f"User {self.scope['user'].username} connecting...")

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        print(f"WebSocket connected: {self.scope['user'].username} ({self.channel_name}) joined group {self.room_group_name}")

        # --- THE CORRECTED FIX IS HERE ---
        # Force the QuerySet to be evaluated into a list *inside* sync_to_async
        messages = await sync_to_async(
            lambda: list(ChatMessage.objects.order_by('-timestamp').select_related('user').all())
        )()
        # --- END CORRECTED FIX ---

        # Reverse to get oldest first for display
        messages_to_send = []
        for message in messages: # This loop now iterates over a plain list, not a lazy QuerySet
            messages_to_send.append({
                'username': message.user.username,
                'message': message.content,
                'timestamp': message.timestamp.isoformat(), # Convert datetime to string
            })
        messages_to_send.reverse() # Display oldest first

        # Send historical messages to the newly connected client
        await self.send(text_data=json.dumps({
            'type': 'chat_history',
            'messages': messages_to_send,
        }))


    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        username = self.scope['user'].username if not self.scope['user'].is_anonymous else 'Anonymous'
        print(f"WebSocket disconnected: {username} ({self.channel_name}) left group {self.room_group_name}")


    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_content = text_data_json['message'] # Renamed to avoid conflict with 'message' object

        user = self.scope["user"]
        username = user.username

        print(f"Received message from {username}: {message_content}")

        # What & Why (Persistence - Saving Message):
        # Save the message to the database
        # Database operations are synchronous, so we need to wrap them with sync_to_async
        chat_message = await sync_to_async(ChatMessage.objects.create)(
            user=user,
            content=message_content
        )

        # Send message to room group (now using the saved message's content and user)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': chat_message.content, # Use content from saved message
                'username': chat_message.user.username, # Use username from saved message's user
                'timestamp': chat_message.timestamp.isoformat(), # Include timestamp
            }
        )

    async def chat_message(self, event):
        message = event['message']
        username = event['username']
        timestamp = event['timestamp'] # Get timestamp from event

        print(f"Sending message to client: {username}: {message}")
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat_message', # Explicitly send type for frontend handling
            'message': message,
            'username': username,
            'timestamp': timestamp, # Send timestamp to frontend
        }))

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # What & Why: Get the user_id from the URL path.
        # This is the ID of the user whose notifications this consumer should handle.
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        # What & Why: Create a unique group name for this specific user's notifications.
        # This allows us to send notifications only to a particular user.
        self.notification_group_name = f'user_notifications_{self.user_id}'

        # What & Why (Authentication & Authorization):
        # 1. Check if the user is authenticated at all.
        # 2. Check if the authenticated user's ID matches the user_id in the URL.
        #    This prevents user A from subscribing to user B's notifications.
        if self.scope["user"].is_anonymous or str(self.scope["user"].id) != self.user_id:
            print(f"Notification WebSocket connection rejected: User {self.scope['user'].username} ({self.scope['user'].id}) tried to connect to user_id {self.user_id}.")
            await self.close()
            return

        print(f"User {self.scope['user'].username} connecting to notifications for ID {self.user_id}...")

        # Join the user-specific notification group
        await self.channel_layer.group_add(
            self.notification_group_name,
            self.channel_name
        )

        await self.accept()

        print(f"Notification WebSocket connected: {self.scope['user'].username} ({self.channel_name}) joined group {self.notification_group_name}")

        # What & Why (Persistence - Loading unread notifications history):
        # Fetch unread notifications for this recipient from the database
        unread_notifications = await sync_to_async(
            lambda: list(Notification.objects.filter(recipient=self.scope["user"], is_read=False).order_by('-timestamp'))
        )()

        notifications_to_send = []
        for notif in unread_notifications:
            notifications_to_send.append({
                'id': notif.id, # Send ID for potential 'mark as read' later
                'message': notif.message,
                'timestamp': notif.timestamp.isoformat(),
            })

        # Send historical unread notifications to the newly connected client
        if notifications_to_send:
            await self.send(text_data=json.dumps({
                'type': 'notification_history',
                'notifications': notifications_to_send,
            }))
            print(f"Sent {len(notifications_to_send)} unread notifications to {self.scope['user'].username}.")


    async def disconnect(self, close_code):
        # Leave the user-specific notification group
        await self.channel_layer.group_discard(
            self.notification_group_name,
            self.channel_name
        )
        username = self.scope['user'].username if not self.scope['user'].is_anonymous else 'Anonymous'
        print(f"Notification WebSocket disconnected: {username} ({self.channel_name}) left group {self.notification_group_name}")

    async def receive(self, text_data):
        # For a simple notification system, the client usually doesn't send messages back
        # (unless for "mark as read" type actions).
        # We'll just log it for now.
        print(f"Received message from notification client {self.scope['user'].username}: {text_data}")

        # Example: If client sends a 'mark_as_read' message
        # data = json.loads(text_data)
        # if data.get('type') == 'mark_as_read' and data.get('id'):
        #     await sync_to_async(Notification.objects.filter(id=data['id'], recipient=self.scope['user']).update)(is_read=True)
        #     print(f"Notification {data['id']} marked as read for {self.scope['user'].username}")


    # What & Why: This method will be called when a new notification is sent
    # from the Django backend via channel_layer.group_send().
    async def send_notification(self, event):
        message = event['message']
        notification_id = event.get('id') # Get ID if sent, for future use

        print(f"Sending live notification to client {self.scope['user'].username}: {message}")
        # Send message directly to the WebSocket client
        await self.send(text_data=json.dumps({
            'type': 'notification', # Explicit type for frontend
            'id': notification_id,
            'message': message,
            'timestamp': event['timestamp'], # Pass timestamp from event
        }))