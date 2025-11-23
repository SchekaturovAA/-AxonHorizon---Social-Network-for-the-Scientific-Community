from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from . import views_friends  # Импортируем новые представления

app_name = 'users'

urlpatterns = [
    # Существующие URL
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='users/logout.html'), name='logout'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('', views.home, name='home'),

    # Новые URL для системы друзей
    path('user/<str:username>/', views_friends.user_profile, name='user_profile'),
    path('friends/', views_friends.friends_list, name='friends_list'),
    path('search/', views_friends.search_users, name='search_users'),
    path('friend-request/send/<str:username>/', views_friends.send_friend_request, name='send_friend_request'),
    path('friend-request/accept/<str:username>/', views_friends.accept_friend_request, name='accept_friend_request'),
    path('friend-request/reject/<str:username>/', views_friends.reject_friend_request, name='reject_friend_request'),
    path('friend-request/cancel/<str:username>/', views_friends.cancel_friend_request, name='cancel_friend_request'),
    path('friend/remove/<str:username>/', views_friends.remove_friend, name='remove_friend'),
]