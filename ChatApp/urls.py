"""
URL configuration for ChatApp project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import loginAPI, signupAPI, getbyIdApi, updateAPI, fetchallusersAPI,addbyemailAPI, getConversationAPI, getAllConversationsAPI ,sendMessageAPI , getConversationMessages ,deleteMessageAPI ,UpdateMessageAPI

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.urls import re_path

schema_view = get_schema_view(
    openapi.Info(
        title="ChatApp Backend API",
        default_version='v1',
        description="Swagger documentation for ChatApp APIs",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)
urlpatterns = [
    path('admin/', admin.site.urls),

    # ===== YOUR APIs =====
    path('signup/', signupAPI.as_view(), name='signup'),
    path('login/', loginAPI.as_view(), name='login'),
    path('get/', getbyIdApi.as_view(), name='get_user'),
    path('update/', updateAPI.as_view(), name='update_user'),
    path('fetchAllUsers/', fetchallusersAPI.as_view()),
    path('addbyemail/', addbyemailAPI.as_view()),

    path('getConversation/', getConversationAPI.as_view()),
    path('getAllConversations/', getAllConversationsAPI.as_view()),
    path('sendMessage/', sendMessageAPI.as_view()),
    path('deleteMessage/', deleteMessageAPI.as_view()), 
    path('updateMessage/', UpdateMessageAPI.as_view()),
    path('getConversationMessages/', getConversationMessages.as_view()),

    # ===== SWAGGER =====
    re_path(r'^swagger(?P<format>\.json|\.yaml)$',
            schema_view.without_ui(cache_timeout=0),
            name='schema-json'),

    path('swagger/',
         schema_view.with_ui('swagger', cache_timeout=0),
         name='schema-swagger-ui'
         ),

    path('redoc/',
         schema_view.with_ui('redoc', cache_timeout=0),
         name='schema-redoc'),
]




if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
