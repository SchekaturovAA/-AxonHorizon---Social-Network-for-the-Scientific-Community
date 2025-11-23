from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.db import transaction
from .forms import UserRegisterForm, UserLoginForm, UserUpdateForm, ProfileUpdateForm
from .models import Profile


def home(request):
    """Главная страница"""
    return render(request, 'users/home.html')


def register(request):
    """Регистрация пользователя"""
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Создаем профиль для пользователя, если его нет
            Profile.objects.get_or_create(user=user)

            # Автоматически логиним пользователя после регистрации
            login(request, user)
            messages.success(request, f'Аккаунт создан для {user.username}!')
            return redirect('users:home')
    else:
        form = UserRegisterForm()

    return render(request, 'users/register.html', {'form': form})


def login_view(request):
    """Вход пользователя"""
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}!')
            return redirect('users:home')
    else:
        form = UserLoginForm()

    return render(request, 'users/login.html', {'form': form})


@login_required
def profile(request):
    """Просмотр профиля"""
    # Создаем профиль, если его нет
    profile, created = Profile.objects.get_or_create(user=request.user)
    if created:
        messages.info(request, 'Профиль был автоматически создан для вас!')

    # Получаем посты пользователя
    user_posts = request.user.posts.all().order_by('-created_at')

    context = {
        'profile': profile,  # Явно передаем профиль в контекст
        'user_posts': user_posts
    }

    return render(request, 'users/profile.html', context)


@login_required
def profile_edit(request):
    """Редактирование профиля"""
    # Создаем профиль, если его нет
    profile, created = Profile.objects.get_or_create(user=request.user)
    if created:
        messages.info(request, 'Профиль был автоматически создан для вас!')

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(
            request.POST,
            request.FILES,
            instance=profile
        )

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Ваш профиль успешно обновлен!')
            return redirect('users:profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form
    }

    return render(request, 'users/profile_edit.html', context)


# Дополнительная функция для создания профилей для существующих пользователей
def create_missing_profiles():
    """Создает профили для пользователей, у которых их нет"""
    from .models import User, Profile
    users_without_profiles = User.objects.filter(profile__isnull=True)
    for user in users_without_profiles:
        Profile.objects.create(user=user)
    return users_without_profiles.count()
