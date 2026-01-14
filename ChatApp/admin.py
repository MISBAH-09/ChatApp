from django.contrib import admin
from .models import User, Message

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'first_name', 'last_name', 'created_at', 'updated_at')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('created_at', 'updated_at')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin): 
    list_display = ('id', 'type', 'body', 'media_url', 'status', 'created_at', 'updated_at')
    search_fields = ('body', 'status')
    list_filter = ('type', 'status', 'created_at', 'updated_at')