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
from .views import loginAPI, signupAPI, getbyIdApi, updateAPI, fetchallusersAPI,getConversationAPI, getAllConversationsAPI
urlpatterns = [
    path('admin/', admin.site.urls),

    path('signup/', signupAPI.as_view(), name='signup'),
    path('login/', loginAPI.as_view(), name='login'),
    path('get/', getbyIdApi.as_view(), name='get_user'),
    path('update/', updateAPI.as_view(), name='update_user'),
    path('fetchallusers/',fetchallusersAPI.as_view()),
    path('getConversation/', getConversationAPI.as_view()),
    path('getAllConversations/',getAllConversationsAPI.as_view())



]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
