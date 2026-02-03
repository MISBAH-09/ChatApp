# ChatApp


ChatApp is a real-time messaging application built with Django and Django Channels. It provides a full-featured backend for one-on-one instant messaging, including user authentication, message handling, and media sharing.

## Features

-   **User Authentication**: Secure user registration and login with token-based authentication (JWT-style).
-   **Real-Time Messaging**: Instant message delivery using WebSockets via Django Channels.
-   **Conversation Management**: Create new conversations, and retrieve all existing conversations for a user.
-   **Rich Media Support**: Send and receive text, image, and audio messages. Media files are handled as base64 strings and stored on the server.
-   **Message Operations**: Update and delete messages, with changes reflected in real-time.
-   **User Profiles**: Users can update their profile information, including their username, name, and profile picture.
-   **Presence System**: Track which users are currently online and broadcast their status.
-   **Asynchronous Email Notifications**: New users added via email receive a welcome message with their credentials. Emails are managed through a persistent queue and sent by a background cron job.
-   **AI Chat Support**: Start and send messages in AI conversations via dedicated API endpoints.
-   **Swagger Docs**: Interactive API documentation powered by Swagger UI and ReDoc.

## Tech Stack

-   **Backend**: Django, Django REST Framework
-   **Real-time Communication**: Django Channels, Daphne (ASGI Server)
-   **Database**: MySQL
-   **Task Scheduling**: `django-crontab` for processing the email queue.
-   **Middleware**: Custom middleware for token-based authentication on both HTTP and WebSocket connections.

## Project Structure

```
├── ChatApp/            # Main Django project
│   ├── views/          # API view logic (users, conversations, messages)
│   ├── middleware/     # Custom authentication middleware
│   ├── models.py       # Core database models
│   ├── settings.py     # Project settings
│   ├── urls.py         # API URL routing (includes Swagger)
│   ├── cron.py         # Cron job for sending emails
│   └── EmailEnqueue.py # Email queue management class
│
├── chats/              # Django app for WebSocket handling
│   ├── consumers.py    # WebSocket consumer logic
│   ├── routing.py      # WebSocket URL routing
│   └── middleware.py   # WebSocket authentication middleware
│
└── media/              # User-uploaded content
    ├── ImgMessages/
    ├── AudioMessages/
    └── profiles/
```

## Setup and Installation

Follow these steps to get the project running on your local machine.

**1. Clone the Repository**

```bash
git clone https://github.com/misbah-09/chatapp.git
cd chatapp
```

**2. Create and Activate a Virtual Environment**

```bash
# For Windows
python -m venv venv
venv\Scripts\activate

# For macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

**3. Install Dependencies**

Create a `requirements.txt` file with the following content and install it:

```
Django
djangorestframework
channels
daphne
mysqlclient
django-cors-headers
python-decouple
django-crontab
drf-yasg
```

```bash
pip install -r requirements.txt
```

**4. Configure Environment Variables**

Create a `.env` file in the root directory and add your configuration details. This project uses `python-decouple` to manage secrets.

```ini
# Database Configuration
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=3306

# Email Configuration (for the cron job)
EMAIL_QUEUE_PATH=D:/path/to/your/project/ChatApp/ChatApp/email_queue.pkl
EMAIL_SENDER=your-email@gmail.com
EMAIL_APP_PASSWORD=your-gmail-app-password
COMET_API_KEY=your-chatbot-apikey
COMET_API_URL=your-chat-bot-api-url
COMET_MODEL=your-chatbot-model
```
*Note: Make sure to update `EMAIL_QUEUE_PATH` to the absolute path on your system.*


**5. Set up the Database**

Run the Django migrations to create the database schema.

```bash
python manage.py makemigrations
python manage.py migrate
```

**6. Install and Run Cron Jobs**

Add the cron job to your system's crontab.

```bash
python manage.py crontab add
```

**7. Run the Application**

Start the Daphne ASGI server.

```bash
daphne ChatApp.asgi:application
```

The server will be running at `http://127.0.0.1:8000`.

## API Endpoints

All protected endpoints require an `Authorization: Bearer <token>` header.

### User Management

| Method | Endpoint          | Description                                         | Authentication |
| :----- | :---------------- | :-------------------------------------------------- | :------------- |
| `POST` | `/signup/`        | Register a new user.                                | None           |
| `POST` | `/login/`         | Log in a user to receive an authentication token.   | None           |
| `GET`  | `/get/`           | Get the profile of the authenticated user.          | Required       |
| `PUT`  | `/update/`        | Update the profile of the authenticated user.       | Required       |
| `GET`  | `/fetchAllUsers/` | Get a list of all users except the current user.    | Required       |
| `POST` | `/addbyemail/`    | Create a new user by email and send welcome message.| None           |

### Conversation & Messaging

| Method | Endpoint                   | Description                                         | Authentication |
| :----- | :------------------------- | :-------------------------------------------------- | :------------- |
| `POST` | `/getConversation/`        | Get or create a conversation with another user.     | Required       |
| `GET`  | `/getAllConversations/`    | Get all conversations for the authenticated user.    | Required       |
| `POST` | `/sendMessage/`            | Send a message to a conversation.                   | Required       |
| `POST` | `/getConversationMessages/`| Get all messages for a specific conversation.       | Required       |
| `POST` | `/deleteMessage/`         | Delete a message sent by the user.                  | Required       |
| `PUT`  | `/updateMessage/`         | Update the body of a text message sent by the user. | Required       |
| `POST` | `/sendMessage/`            | Send a message to a conversation. *(Legacy HTTP; prefer WebSockets)* | Required |

### AI Chat

| Method | Endpoint               | Description                                           | Authentication |
| :----- | :--------------------- | :---------------------------------------------------- | :------------- |
| `POST` | `/getAIConversation/`  | Get or create an AI conversation for the user.        | Required       |
| `POST` | `/sendAIMessage/`      | Send a message in an AI conversation.                 | Required       |

## Swagger Documentation

Interactive docs and schemas are available when the server is running:

-   **Swagger UI**: `/swagger/`
-   **ReDoc**: `/redoc/`
-   **OpenAPI Schema**: `/swagger.json` or `/swagger.yaml`


## WebSocket API

The application uses a single global WebSocket endpoint for real-time communication.

-   **Endpoint**: `ws://127.0.0.1:8000/ws/global/`
-   **Authentication**: Pass the user's token as a query parameter: `ws://127.0.0.1:8000/ws/global/?token=<YOUR_TOKEN>`

### Client-to-Server Events

| Event Type             | Payload                                                                                           | Description                                            |
| :--------------------- | :------------------------------------------------------------------------------------------------ | :----------------------------------------------------- |
| `join_conversation`    | `{"type": "join_conversation", "conversation_id": 123}`                                           | Subscribes the client to a specific conversation channel. |
| `leave_conversation`   | `{"type": "leave_conversation", "conversation_id": 123}`                                          | Unsubscribes the client from a conversation channel.   |
| `chat_message`         | `{ "type": "chat_message", "conversation_id": 123, "msg_type": "text", "body": "Hello", "media": null }` | Sends a message to a conversation.                     |

### Server-to-Client Events

| Event Type          | Payload                                                                                                  | Description                                                          |
| :------------------ | :------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------- |
| `chat_message_event`| A JSON object representing the newly created `Message` model instance.                                   | Broadcasts a new message to all clients in a conversation.           |
| `global_message_event`| A JSON object representing the newly created `Message` instance.                                   | Notifies a user about a message in a conversation they are not currently "joined" to. |
| `connected_users`   | `{ "type": "connected_users", "users": [1, 5, 12] }`                                                      | Broadcasts the list of currently online user IDs.                    |
