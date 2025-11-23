from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.http import JsonResponse
from .models import Community, CommunityMembership
from .forms import CommunityForm, CommunitySettingsForm, RoleChangeForm
from posts.models import Post
from posts.forms import PostForm


@login_required
def community_list(request):
    """Список всех сообществ"""
    communities = Community.objects.all().annotate(
        members_count=models.Count('members'),
        posts_count=models.Count('posts')
    )

    # Сообщества, в которых состоит пользователь
    user_communities = request.user.communities_joined.all() if request.user.is_authenticated else []

    context = {
        'communities': communities,
        'user_communities': user_communities,
    }

    return render(request, 'communities/community_list.html', context)


@login_required
def community_create(request):
    """Создание нового сообщества"""
    if request.method == 'POST':
        form = CommunityForm(request.POST, request.FILES)
        if form.is_valid():
            community = form.save(commit=False)
            community.created_by = request.user
            community.save()

            # Создатель автоматически становится администратором
            CommunityMembership.objects.create(
                user=request.user,
                community=community,
                role='admin'
            )

            messages.success(request, f'Сообщество "{community.name}" успешно создано!')
            return redirect('communities:community_detail', community_id=community.id)
    else:
        form = CommunityForm()

    return render(request, 'communities/community_form.html', {'form': form})


@login_required
def community_detail(request, community_id):
    """Детальная страница сообщества"""
    community = get_object_or_404(Community, id=community_id)
    posts = community.posts.all().order_by('-created_at')

    # Информация о членстве пользователя
    is_member = community.is_member(request.user)
    membership = None
    user_role = None

    if is_member:
        membership = CommunityMembership.objects.filter(user=request.user, community=community).first()
        user_role = membership.role

    # Проверка прав
    can_edit = community.is_creator(request.user) or user_role in ['admin', 'moderator']
    can_manage_members = community.is_creator(request.user) or user_role == 'admin'

    # Форма для поста
    post_form = PostForm()

    context = {
        'community': community,
        'posts': posts,
        'is_member': is_member,
        'membership': membership,
        'user_role': user_role,
        'can_edit': can_edit,
        'can_manage_members': can_manage_members,
        'post_form': post_form,
    }

    return render(request, 'communities/community_detail.html', context)


@login_required
def community_edit(request, community_id):
    """Редактирование сообщества"""
    community = get_object_or_404(Community, id=community_id)

    # Проверка прав
    if not (community.is_creator(request.user) or community.is_moderator(request.user)):
        messages.error(request, 'У вас нет прав для редактирования этого сообщества!')
        return redirect('communities:community_detail', community_id=community.id)

    if request.method == 'POST':
        form = CommunityForm(request.POST, request.FILES, instance=community)
        if form.is_valid():
            form.save()
            messages.success(request, 'Сообщество успешно обновлено!')
            return redirect('communities:community_detail', community_id=community.id)
    else:
        form = CommunityForm(instance=community)

    context = {
        'form': form,
        'community': community,
        'editing': True,
    }

    return render(request, 'communities/community_form.html', context)


@login_required
def community_join(request, community_id):
    """Вступление в сообщество"""
    community = get_object_or_404(Community, id=community_id)

    if community.is_member(request.user):
        messages.info(request, 'Вы уже состоите в этом сообществе!')
    else:
        CommunityMembership.objects.create(user=request.user, community=community)
        messages.success(request, f'Вы вступили в сообщество "{community.name}"!')

    return redirect('communities:community_detail', community_id=community.id)


@login_required
def community_leave(request, community_id):
    """Выход из сообщества"""
    community = get_object_or_404(Community, id=community_id)
    membership = CommunityMembership.objects.filter(user=request.user, community=community).first()

    if membership:
        # Создатель не может покинуть сообщество
        if community.is_creator(request.user):
            messages.error(request, 'Создатель не может покинуть сообщество! Передайте права другому администратору.')
        else:
            membership.delete()
            messages.info(request, f'Вы вышли из сообщества "{community.name}"')
    else:
        messages.info(request, 'Вы не состоите в этом сообществе.')

    return redirect('communities:community_detail', community_id=community.id)


@login_required
def community_members(request, community_id):
    """Управление участниками сообщества"""
    community = get_object_or_404(Community, id=community_id)

    # Проверка прав
    if not (community.is_creator(request.user) or community.is_moderator(request.user)):
        messages.error(request, 'У вас нет прав для управления участниками!')
        return redirect('communities:community_detail', community_id=community.id)

    members = CommunityMembership.objects.filter(community=community).select_related('user')
    role_form = RoleChangeForm()

    context = {
        'community': community,
        'members': members,
        'role_form': role_form,
    }

    return render(request, 'communities/community_members.html', context)


@login_required
def change_member_role(request, community_id, user_id):
    """Изменение роли участника"""
    if request.method == 'POST':
        community = get_object_or_404(Community, id=community_id)
        target_user = CommunityMembership.objects.filter(community=community, user_id=user_id).first()
        if not target_user:
            messages.error(request, 'Участник не найден!')
            return redirect('communities:community_members', community_id=community.id)

        # Только создатель или администраторы могут менять роли
        if not (community.is_creator(request.user) or
                CommunityMembership.objects.get(user=request.user, community=community).role == 'admin'):
            messages.error(request, 'У вас нет прав для изменения ролей!')
            return redirect('communities:community_members', community_id=community.id)

        # Создателя нельзя изменить
        if community.is_creator(target_user.user):
            messages.error(request, 'Нельзя изменить роль создателя сообщества!')
            return redirect('communities:community_members', community_id=community.id)

        form = RoleChangeForm(request.POST, instance=target_user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Роль пользователя {target_user.user.username} изменена!')

    return redirect('communities:community_members', community_id=community.id)


@login_required
def remove_member(request, community_id, user_id):
    """Удаление участника из сообщества"""
    if request.method == 'POST':
        community = get_object_or_404(Community, id=community_id)

        # Проверка прав
        if not (community.is_creator(request.user) or
                CommunityMembership.objects.get(user=request.user, community=community).role == 'admin'):
            messages.error(request, 'У вас нет прав для удаления участников!')
            return redirect('communities:community_members', community_id=community.id)

        target_membership = CommunityMembership.objects.filter(community=community, user_id=user_id).first()
        if not target_membership:
            messages.error(request, 'Участник не найден!')
            return redirect('communities:community_members', community_id=community.id)

        # Создателя нельзя удалить
        if community.is_creator(target_membership.user):
            messages.error(request, 'Нельзя удалить создателя сообщества!')
        else:
            target_membership.delete()
            messages.success(request, f'Пользователь {target_membership.user.username} удален из сообщества!')

    return redirect('communities:community_members', community_id=community.id)


@login_required
def create_community_post(request, community_id):
    """Создание поста в сообществе"""
    community = get_object_or_404(Community, id=community_id)

    # Проверка, что пользователь является участником
    if not community.is_member(request.user):
        messages.error(request, 'Вы должны быть участником сообщества, чтобы публиковать посты!')
        return redirect('communities:community_detail', community_id=community.id)

    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.community = community
            post.save()
            messages.success(request, 'Пост успешно опубликован в сообществе!')
        else:
            messages.error(request, 'Ошибка при создании поста!')

    return redirect('communities:community_detail', community_id=community.id)
