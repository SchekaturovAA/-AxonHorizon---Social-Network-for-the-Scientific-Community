from django.urls import path
from . import views

app_name = 'posts'

urlpatterns = [
    path('create/', views.create_post, name='create_post'),
    path('<int:post_id>/', views.post_detail, name='post_detail'),
    path('<int:post_id>/like/', views.like_post, name='like_post'),
    path('<int:post_id>/delete/', views.delete_post, name='delete_post'),
    path('news-feed/', views.news_feed, name='news_feed'),
    path('favourite/<int:post_id>/', views.toggle_favourite, name='toggle_favourite'),
    path('favourites/', views.favourite_posts, name='favourite_posts'),
] # Добавляем ленту новостей