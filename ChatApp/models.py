from django.db import models

class User(models.Model):
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=20)
    email = models.EmailField(max_length=100, unique=True)
    password = models.CharField(max_length=100, null=True, blank=True)
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    token = models.CharField(max_length=200, null=True, blank=True)
    profile = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Conversations(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100)
    status = models.CharField(max_length=50, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Message(models.Model):
    id = models.AutoField(primary_key=True)
    type = models.CharField(max_length=10)
    body = models.TextField()
    media_url = models.CharField(max_length=200, null=True, blank=True)
    sender_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages')
    conversation_id = models.ForeignKey("Conversations", on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    status = models.CharField(max_length=20)
    is_edited =models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Conversations_Users(models.Model):
    id = models.AutoField(primary_key=True)
    conversation_id= models.ForeignKey("Conversations" , on_delete=models.CASCADE)
    is_group =models.BooleanField(default=False)
    user_ids = models.TextField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class AI_Conversations(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # one-to-one conversation per user
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class AI_Messages(models.Model):
    id = models.AutoField(primary_key=True)
    convo = models.ForeignKey(AI_Conversations, on_delete=models.CASCADE, related_name="messages")
    message = models.TextField()
    sender_is_user = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)