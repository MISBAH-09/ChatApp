from django.db import models

class User(models.Model):  # Existing, adjust if named differently
    id = models.IntegerField(primary_key=True)
    username = models.CharField(max_length=20)
    email = models.CharField(max_length=100)
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    profile = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# class Message(models.Model):  # Existing
#     id = models.IntegerField(primary_key=True)
#     type = models.CharField(max_length=10)
#     body = models.TextField()
#     media_url = models.CharField(max_length=200, null=True, blank=True)
#     user = models.ForeignKey(User, on_delete=models.CASCADE)  # Assuming user_id maps here
#     status = models.CharField(max_length=20)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
