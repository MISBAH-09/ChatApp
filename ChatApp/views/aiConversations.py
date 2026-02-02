import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models import User, AI_Conversations, AI_Messages
from ..middleware.auth import require_token
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

COMET_API_KEY = "sk-qXSgDiOmMC7lwriPimQqAZ3XU0IFcNU9nUSUUm0xa6ry7hnW"
COMET_API_URL = "https://api.cometapi.com/v1/responses"
COMET_MODEL = "gpt-5.2-chat-latest"  # or gpt-5-nano

def generate_ai_reply(user, message: str) -> str:
    """
    Rule-based AI for simple greetings.
    Returns False if message should go to CometAI.
    """
    msg = message.lower()
    if "hi" in msg or "hello" in msg:
        return f"Hello {user.username}, how can I help you? 👋"
    if "help" in msg:
        return "How can i assist you ..!!"
    return False  # Send to CometAI

def get_comet_ai_response(user_message: str) -> str:
    try:
        response = requests.post(
            COMET_API_URL,
            json={
                "model": COMET_MODEL,
                "input": user_message,
                "max_tokens": 150
            },
            headers={
                "Authorization": f"Bearer {COMET_API_KEY}",
                "Content-Type": "application/json"
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        # Flexible content extraction
        if "output" in data and isinstance(data["output"], list) and len(data["output"]) > 0:
            first_item = data["output"][0]
            # Check multiple possible keys
            if "content" in first_item:
                content = first_item["content"]
                if isinstance(content, list) and len(content) > 0:
                    return " ".join([c.get("text", "") for c in content if "text" in c])
                elif isinstance(content, str):
                    return content
            elif "text" in first_item:
                return first_item["text"]

        return "Sorry, AI didn't return a valid response this time."

    except requests.exceptions.Timeout:
        return "Sorry, AI took too long to respond. ⏳"
    except requests.exceptions.RequestException as e:
        return f"Sorry, AI request failed. Error: {str(e)}"
    except Exception as e:
        return f"Sorry, AI is currently unavailable. Error: {str(e)}"
    


class sendAIMessageAPI(APIView):
    @swagger_auto_schema(
        tags=["AI Conversations"],
        operation_summary="Send a message to AI",
        operation_description="Store user message and generate AI reply.",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Bearer your_token_here",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['message'],
            properties={
                'message': openapi.Schema(type=openapi.TYPE_STRING, example="Hi AI", description="User message"),
                'conversation_id': openapi.Schema(type=openapi.TYPE_STRING, example="1", description="Conversation ID")
            }
        ),
        responses={
            200: "Message sent and AI reply returned",
            400: "Validation error",
            401: "Unauthorized"
        }
    )
    @require_token
    def post(self, request):
        try:
            user = request.auth_user
            user_message = request.data.get("message", "").strip()
            conversation_id = request.data.get("conversation_id")

            if not user_message:
                return Response({"success": False, "error": "Message cannot be empty"}, status=400)
            if not conversation_id:
                return Response({"success": False, "error": "Conversation ID is required"}, status=400)

            # Get conversation
            conversation = AI_Conversations.objects.get(id=conversation_id)

            # Store user message
            AI_Messages.objects.create(
                convo=conversation,
                message=user_message,
                sender_is_user=True
            )

            # Determine AI reply
            ai_reply = generate_ai_reply(user, user_message)
            if not ai_reply:
                # Send to CometAI if rule-based reply not found
                ai_reply = get_comet_ai_response(user_message)

            # Store AI reply
            AI_Messages.objects.create(
                convo=conversation,
                message=ai_reply,
                sender_is_user=False
            )

            # Fetch all messages
            messages = conversation.messages.all().order_by("created_at")
            messages_data = [
                {
                    "id": m.id,
                    "text": m.message,
                    "sender": "user" if m.sender_is_user else "ai",
                    "created_at": m.created_at
                }
                for m in messages
            ]

            return Response({
                "success": True,
                "conversation_id": conversation.id,
                "messages": messages_data
            }, status=200)

        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=400)

class getAIConversationAPI(APIView):
  @swagger_auto_schema(
    tags=["AI Conversations"],
    operation_summary="Get or create AI conversation",
    operation_description="Fetch existing AI conversation or create a new one with initial greeting.",
    manual_parameters=[
      openapi.Parameter(
        'Authorization',
        openapi.IN_HEADER,
        description="Bearer your_token_here",
        type=openapi.TYPE_STRING,
        required=True
      )
    ],
    responses={
      200: "Conversation exists, messages returned",
      201: "New conversation created with initial AI greeting",
      400: "Validation error",
      401: "Unauthorized"
    }
  )
  @require_token
  def get(self, request):
    try:
      user = request.auth_user
      #  Get or create conversation
      conversation = AI_Conversations.objects.filter(user=user).first()
      if not conversation:
        conversation = AI_Conversations.objects.create(user=user)
        # Add initial AI greeting
        AI_Messages.objects.create(
          convo=conversation,
          message=f"Hello {user.username}, how can I help you? 👋",
          sender_is_user=False
        )
        status_code = status.HTTP_201_CREATED
      else:
        status_code = status.HTTP_200_OK

      # 2️⃣ Fetch all messages
      messages = conversation.messages.all().order_by("created_at")
      messages_data = [
        {"id": m.id, "text": m.message, "sender": "user" if m.sender_is_user else "ai", "created_at": m.created_at}
        for m in messages
      ]

      return Response({
        "success": True,
        "conversation_id": conversation.id,
        "messages": messages_data
      }, status=status_code)

    except Exception as e:
      return Response({"success": False, "error": str(e)}, status=400)

# class sendAIMessageAPI(APIView):
#   @swagger_auto_schema(
#       tags=["AI Conversations"],
#       operation_summary="Send a message to AI",
#       operation_description="Store user message and generate AI reply.",
#       manual_parameters=[
#           openapi.Parameter(
#               'Authorization',
#               openapi.IN_HEADER,
#               description="Bearer your_token_here",
#               type=openapi.TYPE_STRING,
#               required=True
#           )
#       ],
#       request_body=openapi.Schema(
#           type=openapi.TYPE_OBJECT,
#           required=['message'],
#           properties={
#               'message': openapi.Schema(type=openapi.TYPE_STRING, example="Hi AI", description="User message")
#           }
#       ),
#       responses={
#           200: "Message sent and AI reply returned",
#           400: "Validation error",
#           401: "Unauthorized"
#       }
#   )
#   @require_token
#   def post(self, request):
      try:
          user = request.auth_user
          user_message = request.data.get("message", "").strip()
          conversation_id = request.data.get("conversation_id")

          if not user_message:
              return Response({"success": False, "error": "Message cannot be empty"}, status=400)
          if not conversation_id:
              return Response({"success": False, "error": "Conversation ID is required"}, status=400)

          # Get conversation
          conversation = AI_Conversations.objects.get(id=conversation_id)

          # Store user message
          AI_Messages.objects.create(
              convo=conversation,
              message=user_message,
              sender_is_user=True
          )

          #  Generate AI reply using the separate function
          ai_reply = generate_ai_reply(user, user_message)

          # Store AI reply
          AI_Messages.objects.create(
              convo=conversation,
              message=ai_reply,
              sender_is_user=False
          )

          #  Fetch all messages
          messages = conversation.messages.all().order_by("created_at")
          messages_data = [
              {
                  "id": m.id,
                  "text": m.message,
                  "sender": "user" if m.sender_is_user else "ai",
                  "created_at": m.created_at
              }
              for m in messages
          ]

          return Response({
              "success": True,
              "conversation_id": conversation.id,
              "messages": messages_data
          }, status=200)

      except Exception as e:
          return Response({"success": False, "error": str(e)}, status=400)