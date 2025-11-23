from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Q, Count
from django.db import models
from django.conf import settings
from django.utils import timezone
from .models import Chat, ChatMember, Message, MessageRead
from .forms import ChatForm, MessageForm, AddMembersForm
from users.models import User
from utils.mongo_cache import MongoCacheHelper
import time


@login_required
def chat_list(request):
    """Список чатов пользователя с кэшированием"""
    # Пробуем получить из кэша MongoDB
    cached_data = MongoCacheHelper.get_cached_chat_list(request.user.id)

    if cached_data:
        print("✅ Список чатов получен из кэша MongoDB")
        return render(request, 'chats/chat_list.html', cached_data)

    print("🔄 Список чатов загружается из базы данных")

    # Основной запрос для получения чатов пользователя
    user_chats = Chat.objects.filter(members=request.user).annotate(
        message_count=Count('messages'),
        last_message_time=models.Max('messages__created_at')
    ).order_by('-updated_at')

    # Добавляем информацию о непрочитанных сообщениях для каждого чата
    for chat in user_chats:
        try:
            chat_member = ChatMember.objects.get(chat=chat, user=request.user)
            unread_count = Message.objects.filter(
                chat=chat,
                created_at__gt=chat_member.last_read
            ).count()
            chat.unread_count = unread_count
        except ChatMember.DoesNotExist:
            chat.unread_count = 0

    # Подготавливаем контекст для кэширования
    context = {
        'chats': user_chats,
        'cache_timestamp': time.time()  # Метка времени для отладки
    }

    # Сохраняем в кэш MongoDB на 5 минут
    MongoCacheHelper.cache_chat_list(request.user.id, context)

    return render(request, 'chats/chat_list.html', context)


@login_required
def chat_detail(request, chat_id):
    """Детальная страница чата с сообщениями и кэшированием"""
    chat = get_object_or_404(Chat, id=chat_id, members=request.user)

    # Пробуем получить сообщения из кэша MongoDB
    cached_messages = MongoCacheHelper.get_cached_chat_messages(chat_id)

    if cached_messages:
        print("✅ Сообщения чата получены из кэша MongoDB")
        messages_list = cached_messages
    else:
        print("🔄 Сообщения чата загружаются из базы данных")
        messages_list = list(chat.messages.all().order_by('created_at'))
        # Сохраняем в кэш MongoDB на 5 минут
        MongoCacheHelper.cache_chat_messages(chat_id, messages_list)

    # Помечаем сообщения как прочитанные для текущего пользователя
    try:
        chat_member = ChatMember.objects.get(chat=chat, user=request.user)
        unread_messages = chat.messages.filter(created_at__gt=chat_member.last_read)

        # Создаем записи о прочтении для непрочитанных сообщений
        for message in unread_messages:
            MessageRead.objects.get_or_create(user=request.user, message=message)

        # Обновляем время последнего прочтения
        chat_member.last_read = timezone.now()
        chat_member.save()
    except ChatMember.DoesNotExist:
        pass

    # Обработка отправки нового сообщения
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.chat = chat
            message.author = request.user
            message.save()

            # Инвалидируем кэш чата при отправке нового сообщения
            MongoCacheHelper.invalidate_chat_cache(chat_id)

            # Для AJAX запросов возвращаем JSON
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success'})

            # Для обычных запросов - редирект
            return redirect('chats:chat_detail', chat_id=chat.id)
    else:
        form = MessageForm()

    # Формируем контекст
    context = {
        'chat': chat,
        'messages_list': messages_list,
        'form': form,
        'cache_timestamp': time.time()  # Метка времени для отладки
    }

    return render(request, 'chats/chat_detail.html', context)


@login_required
def create_chat(request):
    """Создание группового чата"""
    if request.method == 'POST':
        form = ChatForm(request.POST)
        if form.is_valid():
            # Создаем чат
            chat = form.save(commit=False)
            chat.chat_type = 'group'  # Принудительно устанавливаем тип "групповой"
            chat.created_by = request.user
            chat.save()

            # Добавляем создателя в чат как администратора
            ChatMember.objects.create(user=request.user, chat=chat, role='admin')

            # Добавляем выбранных пользователей
            user_ids = request.POST.getlist('users')
            added_users_count = 0
            for user_id in user_ids:
                try:
                    user = User.objects.get(id=user_id)
                    ChatMember.objects.get_or_create(user=user, chat=chat)
                    added_users_count += 1

                    # Инвалидируем кэш списка чатов для добавленного пользователя
                    MongoCacheHelper.invalidate_user_cache(user.id)
                except User.DoesNotExist:
                    continue

            # Инвалидируем кэш списка чатов для создателя
            MongoCacheHelper.invalidate_user_cache(request.user.id)

            # Сообщения об успехе
            if added_users_count > 0:
                messages.success(request, f"Групповой чат создан! Добавлено {added_users_count} участников")
            else:
                messages.success(request, "Групповой чат создан! Вы можете добавить участников в настройках чата")

            return redirect('chats:chat_detail', chat_id=chat.id)
        else:
            messages.error(request, "Пожалуйста, исправьте ошибки в форме")
    else:
        form = ChatForm(initial={'chat_type': 'group'})

    # Список друзей для добавления в групповой чат
    friends = request.user.get_friends()

    context = {
        'form': form,
        'friends': friends,
    }
    return render(request, 'chats/create_chat.html', context)


@login_required
def chat_settings(request, chat_id):
    """Настройки чата"""
    chat = get_object_or_404(Chat, id=chat_id, members=request.user)

    # Проверяем права пользователя (только админы могут менять настройки)
    try:
        user_membership = ChatMember.objects.get(chat=chat, user=request.user)
        user_role = user_membership.role
        if user_role != 'admin' and chat.created_by != request.user:
            messages.error(request, "У вас нет прав для изменения настроек чата")
            return redirect('chats:chat_detail', chat_id=chat.id)
    except ChatMember.DoesNotExist:
        messages.error(request, "У вас нет прав для изменения настроек чата")
        return redirect('chats:chat_detail', chat_id=chat.id)

    if request.method == 'POST':
        # Обработка добавления участников
        if 'add_members' in request.POST:
            add_form = AddMembersForm(request.POST, current_chat=chat)
            if add_form.is_valid():
                users = add_form.cleaned_data['users']
                added_count = 0
                for user in users:
                    _, created = ChatMember.objects.get_or_create(user=user, chat=chat)
                    if created:
                        added_count += 1
                        # Инвалидируем кэш для добавленного пользователя
                        MongoCacheHelper.invalidate_user_cache(user.id)

                if added_count > 0:
                    messages.success(request, f"Добавлено {added_count} участников")
                    # Инвалидируем кэш чата
                    MongoCacheHelper.invalidate_chat_cache(chat_id)
                else:
                    messages.info(request, "Все выбранные пользователи уже были участниками чата")
                return redirect('chats:chat_settings', chat_id=chat.id)
            else:
                messages.error(request, "Пожалуйста, исправьте ошибки в форме")
        else:
            # Обработка изменения настроек чата
            form = ChatForm(request.POST, instance=chat)
            if form.is_valid():
                form.save()
                messages.success(request, "Настройки чата обновлены")
                # Инвалидируем кэш чата
                MongoCacheHelper.invalidate_chat_cache(chat_id)
                return redirect('chats:chat_settings', chat_id=chat.id)
            else:
                messages.error(request, "Пожалуйста, исправьте ошибки в форме")
    else:
        form = ChatForm(instance=chat)
        add_form = AddMembersForm(current_chat=chat)

    # Получаем список участников чата
    members = ChatMember.objects.filter(chat=chat).select_related('user')

    context = {
        'chat': chat,
        'form': form,
        'add_form': add_form,
        'members': members,
    }
    return render(request, 'chats/chat_settings.html', context)


@login_required
def search_users(request):
    """Поиск пользователей для добавления в чат"""
    query = request.GET.get('q', '')
    if query:
        users = User.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        ).exclude(id=request.user.id)[:10]
        results = [{'id': user.id, 'name': user.get_full_name() or user.username} for user in users]
    else:
        results = []

    return JsonResponse(results, safe=False)


@login_required
def remove_member(request, chat_id, user_id):
    """Удаление участника из чата"""
    chat = get_object_or_404(Chat, id=chat_id, members=request.user)
    user_to_remove = get_object_or_404(User, id=user_id)

    # Проверяем права пользователя
    try:
        user_membership = ChatMember.objects.get(chat=chat, user=request.user)
        user_role = user_membership.role
        if user_role != 'admin' and chat.created_by != request.user:
            messages.error(request, "У вас нет прав для удаления участников")
            return redirect('chats:chat_settings', chat_id=chat.id)
    except ChatMember.DoesNotExist:
        messages.error(request, "У вас нет прав для удаления участников")
        return redirect('chats:chat_settings', chat_id=chat.id)

    # Не позволяем пользователю удалить себя из чата
    if user_to_remove == request.user:
        messages.error(request, "Вы не можете удалить себя из чата")
    else:
        # Удаляем участника
        ChatMember.objects.filter(chat=chat, user=user_to_remove).delete()
        messages.success(request,
                         f"Пользователь {user_to_remove.get_full_name() or user_to_remove.username} удален из чата")

        # Инвалидируем кэш для удаленного пользователя
        MongoCacheHelper.invalidate_user_cache(user_to_remove.id)
        # Инвалидируем кэш чата
        MongoCacheHelper.invalidate_chat_cache(chat_id)

    return redirect('chats:chat_settings', chat_id=chat.id)


@login_required
def create_personal_chat(request, user_id):
    """Быстрое создание личного чата с пользователем"""
    other_user = get_object_or_404(User, id=user_id)

    # Нельзя создать чат с самим собой
    if other_user == request.user:
        messages.error(request, "Нельзя создать чат с самим собой")
        return redirect('users:user_profile', username=request.user.username)

    # Проверяем, не существует ли уже личный чат между этими пользователями
    existing_chat = Chat.objects.filter(
        chat_type='personal',
        members=request.user
    ).filter(members=other_user).distinct().first()

    if existing_chat:
        # Если чат уже существует, перенаправляем в него
        messages.info(request, "Переход к существующему чату")
        return redirect('chats:chat_detail', chat_id=existing_chat.id)

    # Создаем новый личный чат
    chat = Chat.objects.create(
        chat_type='personal',
        created_by=request.user
    )

    # Добавляем обоих пользователей в чат
    ChatMember.objects.create(user=request.user, chat=chat, role='admin')
    ChatMember.objects.create(user=other_user, chat=chat, role='member')

    # Инвалидируем кэш списка чатов для обоих пользователей
    MongoCacheHelper.invalidate_user_cache(request.user.id)
    MongoCacheHelper.invalidate_user_cache(other_user.id)

    messages.success(request, f"Чат с {other_user.get_full_name() or other_user.username} создан")
    return redirect('chats:chat_detail', chat_id=chat.id)


# Вспомогательная функция для получения количества непрочитанных чатов
def get_unread_chats_count(user):
    """Получить количество чатов с непрочитанными сообщениями"""
    if not user.is_authenticated:
        return 0

    user_chats = Chat.objects.filter(members=user)
    unread_count = 0

    for chat in user_chats:
        try:
            chat_member = ChatMember.objects.get(chat=chat, user=user)
            unread_messages = Message.objects.filter(
                chat=chat,
                created_at__gt=chat_member.last_read
            ).count()
            if unread_messages > 0:
                unread_count += 1
        except ChatMember.DoesNotExist:
            continue

    return unread_count