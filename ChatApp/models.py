from django.db import models

class User(models.Model):  # Existing, adjust if named differently
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=20)
    email = models.CharField(max_length=100)
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    token = models.CharField(max_length=200, null=True, blank=True)
    profile = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Message(models.Model):
    id = models.AutoField(primary_key=True)
    type = models.CharField(max_length=10)
    body = models.TextField()
    media_url = models.CharField(max_length=200, null=True, blank=True)
    #updating as foreign key
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages', null=True, blank=True)
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
