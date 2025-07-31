# Django Channels Real-time Chat & Notifications

A simple, educational web application built with Django Channels and WebSockets to demonstrate real-time communication, user authentication, message persistence, and user-specific notifications. This project is ideal for understanding the core concepts of asynchronous Django development.

## Table of Contents

- [Features](#features)
- [Technologies Used](#technologies-used)
- [Setup Instructions](#setup-instructions)
- [How to Run](#how-to-run)
- [Usage](#usage)
- [Known Issues / Limitations](#known-issues--limitations)
- [Future Enhancements](#future-enhancements)
- [Contributing](#contributing)
- [License](#license)

## Features

*   **Real-time Public Chat:** Users can send and receive messages instantly in a public chat room.
*   **User Authentication:** Only logged-in users can participate in the chat and receive notifications.
*   **Chat Message Persistence:** All chat messages are saved to a database and loaded as history when a user connects or refreshes the page.
*   **User-Specific Notifications:** Backend events can trigger real-time notifications that are intended for specific users, with persistence for unread notifications.
*   **ASGI-based:** Leverages Django Channels' Asynchronous Server Gateway Interface for handling WebSockets.

## Technologies Used

*   **Python 3.x**
*   **Django**: The web framework.
*   **Django Channels**: Extends Django to handle asynchronous protocols like WebSockets.
*   **Daphne**: An ASGI HTTP and WebSocket protocol server for Django Channels.
*   **`asgiref`**: ASGI utilities, including `sync_to_async` for bridging synchronous (DB) and asynchronous (Channels) code.
*   **`InMemoryChannelLayer`**: The channel layer backend used for development (see [Known Issues](#known-issues--limitations)).
*   **SQLite**: Default database for development.
*   **HTML, CSS, JavaScript**: For the frontend user interface.

## Setup Instructions

Follow these steps to get the project running on your local machine.

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/your-username/mychatproject.git # Replace with your actual repo URL
    cd mychatproject
    ```

2.  **Create and Activate a Virtual Environment:**
    ```bash
    python -m venv venv
    # On Windows:
    venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install django channels daphne
    ```

4.  **Run Database Migrations:**
    This will create the necessary database tables for Django's auth system, your `ChatMessage` model, and your `Notification` model.
    ```bash
    python manage.py makemigrations chat
    python manage.py migrate
    ```

5.  **Create a Superuser:**
    You'll need at least one user to log in and test the chat/notifications.
    ```bash
    python manage.py createsuperuser
    ```
    Follow the prompts to set up a username, email, and password. You can create more users via the Django admin later.

## How to Run

Since this project uses Django Channels, you'll run it with the Daphne ASGI server.

1.  **Ensure no other process is using port 8000 or 6379.**
    (If you previously ran an old Redis server, ensure it's stopped/disabled.)

2.  **Start the Daphne Server:**
    ```bash
    daphne mysite.asgi:application
    ```
    Daphne will start listening on `http://127.0.0.1:8000`.

## Usage

### 1. Accessing the Chat & Notification Page

1.  Open your web browser.
2.  Go to the Django Admin: `http://127.0.0.1:8000/admin/`
3.  Log in with the superuser (or any user you've created).
4.  In the **same browser**, open a new tab and navigate to the chat page: `http://127.0.0.1:8000/chat/`

    *   You should see "Connected to chat." and "Connected to notifications." in the respective log areas. If you see "Cannot connect to notifications: User ID missing", ensure you are logged in and refresh the page.

### 2. Using the Chat

*   Type a message in the input field and click "Send" or press Enter.
*   The message should appear in the `Public Chat Room` log, prefixed with your username and a timestamp.
*   **To test real-time chat:** Open another browser tab (or even a different browser like Firefox/Chrome) and log in as a *different user* via `/admin/`, then navigate to `/chat/`. Messages sent from one tab should instantly appear in the other.
*   **To test chat history:** Send a few messages, then refresh the page. The messages should reappear as "Chat History" loaded from the database.

### 3. Triggering Notifications

Notifications are user-specific and triggered by backend events. For testing, we have a special URL:

1.  **Identify the Recipient User's ID:**
    *   In your browser, go to `http://127.0.0.1:8000/admin/`.
    *   Log in as your superuser.
    *   Go to "Users" (under `AUTHENTICATION AND AUTHORIZATION`).
    *   Click on the user you want to send a notification *to* (e.g., `prachi`).
    *   The user's ID is in the URL (e.g., `.../auth/user/2/change/` means ID `2`).

2.  **Ensure Recipient is Online:**
    *   Make sure the recipient user (e.g., `prachi`) is logged in and has the `http://127.0.0.1:8000/chat/` page open in their browser.

3.  **Trigger the Notification:**
    *   Open a *separate* browser tab or window (you don't need to be logged in here).
    *   In the address bar, type: `http://127.0.0.1:8000/trigger-notification/YOUR_RECIPIENT_USER_ID/`
    *   Replace `YOUR_RECIPIENT_USER_ID` with the actual ID you found (e.g., `http://127.0.0.1:8000/trigger-notification/2/`).
    *   Press Enter.

4.  **Observe:**
    *   The recipient's browser (the one with `/chat/` open) should immediately show a JavaScript `alert()` pop-up and the notification will appear in the "Notifications" log on the page.
    *   In your Daphne console, you'll see messages indicating the notification was sent.
    *   **To test notification persistence:** Send a few notifications, then log out the recipient, log back in, and visit `/chat/`. The unread notifications should appear in the log.

## Known Issues / Limitations

This project uses the `InMemoryChannelLayer` for simplicity during development. This has a significant limitation:

*   **Notifications may leak to all connected users:** When multiple users are logged in and connected to the chat/notification WebSockets, a user-specific notification (e.g., for `prachi`) might erroneously appear for *all* other connected users (e.g., `aman`). This is due to the inherent nature of the `InMemoryChannelLayer` which does not provide strict isolation between different channel layer groups when running in a single process.
*   **No Scalability:** The `InMemoryChannelLayer` is not suitable for production. If you were to run multiple Daphne processes (for load balancing), they would not be able to communicate, and messages would not be shared between users connected to different processes.
*   **No Persistence for Channel Layer State:** If the Daphne server restarts, any "in-flight" messages in the channel layer are lost (though messages persisted to the database will be reloaded as history).

**For a robust, production-ready solution, you MUST replace `InMemoryChannelLayer` with a proper, external channel layer like `channels_redis` backed by a running Redis server.**

## Future Enhancements

*   **Private Messaging:** Implement private chat rooms between two users.
*   **Mark Notifications as Read:** Add functionality for users to dismiss or mark notifications as read.
*   **Better Frontend UI/UX:** Enhance the styling and interactivity of the chat and notification displays.
*   **Deployment:** Configure for production using Nginx/Gunicorn/Daphne and a robust Redis server.
*   **Error Handling:** More sophisticated error handling for WebSocket disconnections.
*   **Typing Indicators:** Show when other users are typing.

## Contributing

Feel free to fork this repository, make improvements, and submit pull requests. Any contributions are welcome, especially for educational purposes!

## License

This project is open-source and available under the [MIT License](LICENSE).
