from django.urls import path
from . import views

app_name = 'chats'

urlpatterns = [
    path('', views.chat_list, name='chat_list'),
    path('create/', views.create_chat, name='create_chat'),  # Только групповые чаты
    path('create-personal/<int:user_id>/', views.create_personal_chat, name='create_personal_chat'),
    path('<int:chat_id>/', views.chat_detail, name='chat_detail'),
    path('<int:chat_id>/settings/', views.chat_settings, name='chat_settings'),
    path('<int:chat_id>/remove-member/<int:user_id>/', views.remove_member, name='remove_member'),
    path('search-users/', views.search_users, name='search_users'),
]