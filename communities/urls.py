from django.urls import path
from . import views

app_name = 'communities'

urlpatterns = [
    path('', views.community_list, name='community_list'),
    path('create/', views.community_create, name='community_create'),
    path('<int:community_id>/', views.community_detail, name='community_detail'),
    path('<int:community_id>/edit/', views.community_edit, name='community_edit'),
    path('<int:community_id>/join/', views.community_join, name='community_join'),
    path('<int:community_id>/leave/', views.community_leave, name='community_leave'),
    path('<int:community_id>/members/', views.community_members, name='community_members'),
    path('<int:community_id>/members/<int:user_id>/change-role/', views.change_member_role, name='change_member_role'),
    path('<int:community_id>/members/<int:user_id>/remove/', views.remove_member, name='remove_member'),
    path('<int:community_id>/create-post/', views.create_community_post, name='create_community_post'),
]