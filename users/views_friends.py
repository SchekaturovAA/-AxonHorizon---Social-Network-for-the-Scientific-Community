from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import models
from .models import User, Friendship


@login_required
def user_profile(request, username):
    """Просмотр профиля другого пользователя"""
    user = get_object_or_404(User, username=username)

    # Статистика
    posts_count = user.posts.count()
    friends_count = user.get_friends_count()

    # Статус дружбы с текущим пользователем
    friendship_status = None
    if request.user != user:
        if request.user.is_friends_with(user):
            friendship_status = 'friends'
        elif request.user.has_pending_request_to(user):
            friendship_status = 'request_sent'
        elif request.user.has_pending_request_from(user):
            friendship_status = 'request_received'
        else:
            friendship_status = 'not_friends'

    context = {
        'profile_user': user,
        'posts_count': posts_count,
        'friends_count': friends_count,
        'friendship_status': friendship_status,
    }

    return render(request, 'users/user_profile.html', context)


@login_required
def send_friend_request(request, username):
    """Отправить запрос дружбы"""
    if request.method == 'POST':
        to_user = get_object_or_404(User, username=username)

        if request.user == to_user:
            messages.error(request, 'Нельзя отправить запрос дружбы самому себе!')
            return redirect('users:user_profile', username=username)

        # Проверяем, не существует ли уже запрос
        existing_request = Friendship.objects.filter(
            models.Q(from_user=request.user, to_user=to_user) |
            models.Q(from_user=to_user, to_user=request.user)
        ).first()

        if existing_request:
            if existing_request.status == 'pending':
                if existing_request.from_user == request.user:
                    messages.info(request, 'Запрос дружбы уже отправлен!')
                else:
                    messages.info(request, 'У вас уже есть входящий запрос от этого пользователя!')
            elif existing_request.status == 'accepted':
                messages.info(request, 'Вы уже друзья с этим пользователем!')
            else:
                messages.info(request, 'Запрос дружбы был отклонен!')
        else:
            # Создаем новый запрос
            Friendship.objects.create(from_user=request.user, to_user=to_user)
            messages.success(request, f'Запрос дружбы отправлен пользователю {to_user.username}!')

        return redirect('users:user_profile', username=username)

    return redirect('users:user_profile', username=username)


@login_required
def accept_friend_request(request, username):
    """Принять запрос дружбы"""
    if request.method == 'POST':
        from_user = get_object_or_404(User, username=username)
        friendship = get_object_or_404(
            Friendship,
            from_user=from_user,
            to_user=request.user,
            status='pending'
        )

        friendship.accept()
        messages.success(request, f'Вы теперь друзья с {from_user.username}!')

    return redirect('users:friends_list')


@login_required
def reject_friend_request(request, username):
    """Отклонить запрос дружбы"""
    if request.method == 'POST':
        from_user = get_object_or_404(User, username=username)
        friendship = get_object_or_404(
            Friendship,
            from_user=from_user,
            to_user=request.user,
            status='pending'
        )

        friendship.reject()
        messages.info(request, f'Запрос дружбы от {from_user.username} отклонен')

    return redirect('users:friends_list')


@login_required
def cancel_friend_request(request, username):
    """Отменить отправленный запрос дружбы"""
    if request.method == 'POST':
        to_user = get_object_or_404(User, username=username)
        friendship = get_object_or_404(
            Friendship,
            from_user=request.user,
            to_user=to_user,
            status='pending'
        )

        friendship.delete()
        messages.info(request, f'Запрос дружбы пользователю {to_user.username} отменен')

    return redirect('users:user_profile', username=username)


@login_required
def remove_friend(request, username):
    """Удалить из друзей"""
    if request.method == 'POST':
        friend = get_object_or_404(User, username=username)

        # Находим и удаляем связь дружбы в обе стороны
        friendship = Friendship.objects.filter(
            models.Q(from_user=request.user, to_user=friend, status='accepted') |
            models.Q(from_user=friend, to_user=request.user, status='accepted')
        ).first()

        if friendship:
            friendship.delete()
            messages.info(request, f'{friend.username} удален из друзей')
        else:
            messages.error(request, 'Пользователь не найден в списке друзей')

    return redirect('users:friends_list')


@login_required
def friends_list(request):
    """Список друзей и запросов"""
    friends = request.user.get_friends()
    pending_requests = request.user.get_pending_requests()
    sent_requests = request.user.get_sent_requests()

    context = {
        'friends': friends,
        'pending_requests': pending_requests,
        'sent_requests': sent_requests,
    }

    return render(request, 'users/friends_list.html', context)


@login_required
def search_users(request):
    """Поиск пользователей"""
    query = request.GET.get('q', '')
    users = User.objects.all()

    if query:
        users = users.filter(
            models.Q(username__icontains=query) |
            models.Q(first_name__icontains=query) |
            models.Q(last_name__icontains=query) |
            models.Q(email__icontains=query)
        ).exclude(id=request.user.id)

    context = {
        'users': users,
        'query': query,
    }

    return render(request, 'users/search_users.html', context)