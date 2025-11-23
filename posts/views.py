from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import JsonResponse
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from .models import Post, FavouritePost, Comment, PostLike
from .forms import PostForm, CommentForm
from users.models import ScientificField
from utils.mongo_cache import MongoCacheHelper
import time


@login_required
def create_post(request):
    """Создание нового поста"""
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()

            # Инвалидируем кэш ленты новостей для всех пользователей
            # В реальном приложении нужно инвалидировать более точно
            MongoCacheHelper.invalidate_user_cache(request.user.id)

            messages.success(request, "Пост успешно создан!")
            return redirect('posts:news_feed')
    else:
        form = PostForm()

    context = {
        'form': form,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def news_feed(request):
    """Лента новостей - посты из сообществ пользователя и его друзей"""
    # Получаем параметры для кэширования
    content_type = request.GET.get('type', 'all')
    page_number = request.GET.get('page', 1)

    # Пробуем получить из кэша
    cache_key = f"{request.user.id}_{content_type}_{page_number}"
    cached_data = MongoCacheHelper.get_cached_news_feed(request.user.id, content_type, page_number)

    if cached_data:
        print("✅ Данные ленты получены из кэша MongoDB")
        return render(request, 'posts/news_feed.html', cached_data)

    print("🔄 Данные ленты загружаются из базы данных")

    # Сообщества, в которых состоит пользователь
    user_communities = request.user.communities_joined.all()

    # Посты из сообществ пользователя
    community_posts = Post.objects.filter(community__in=user_communities)

    # Посты друзей
    friends_posts = Post.objects.none()
    if hasattr(request.user, 'get_friends'):
        friends = request.user.get_friends()
        friends_posts = Post.objects.filter(author__in=friends, community__isnull=True)

    # Применяем фильтрацию
    if content_type == 'communities':
        all_posts = community_posts
    elif content_type == 'friends':
        all_posts = friends_posts
    else:
        all_posts = (community_posts | friends_posts).distinct()

    # Аннотируем посты
    all_posts = all_posts.annotate(
        like_count=Count('post_likes'),
        comment_count=Count('comments'),
        favourite_count=Count('favourited_by')
    ).order_by('-created_at')

    # Пагинация
    paginator = Paginator(all_posts, 20)
    page_obj = paginator.get_page(page_number)

    # Получаем ID избранных постов пользователя
    user_favourite_ids = []
    if request.user.is_authenticated:
        user_favourites = FavouritePost.objects.filter(
            user=request.user,
            post_id__in=[post.id for post in page_obj]
        )
        user_favourite_ids = [favourite.post_id for favourite in user_favourites]

    # Подготавливаем данные для кэширования
    context = {
        'page_obj': page_obj,
        'community_count': user_communities.count(),
        'content_type': content_type,
        'has_friends': hasattr(request.user, 'get_friends') and request.user.get_friends().exists(),
        'user_favourite_ids': user_favourite_ids,
        'cache_timestamp': time.time()  # Добавляем метку времени
    }

    # Сохраняем в кэш
    MongoCacheHelper.cache_news_feed(request.user.id, content_type, page_number, context)

    return render(request, 'posts/news_feed.html', context)


@login_required
def toggle_favourite(request, post_id):
    """Добавление/удаление поста из избранного"""
    post = get_object_or_404(Post, id=post_id)
    favourite, created = FavouritePost.objects.get_or_create(
        user=request.user,
        post=post
    )

    # Инвалидируем кэш избранных постов
    MongoCacheHelper.invalidate_user_cache(request.user.id)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if not created:
            favourite.delete()
            return JsonResponse({
                'status': 'removed',
                'favourite_count': post.favourited_by.count()
            })
        return JsonResponse({
            'status': 'added',
            'favourite_count': post.favourited_by.count()
        })

    if not created:
        favourite.delete()
        messages.info(request, "Пост удален из избранного")
    else:
        messages.success(request, "Пост добавлен в избранное")

    return redirect(request.META.get('HTTP_REFERER', 'posts:news_feed'))


@login_required
def favourite_posts(request):
    """Страница с избранными постами пользователя"""
    # Параметры фильтрации
    scientific_field_id = request.GET.get('scientific_field')
    post_type = request.GET.get('post_type')

    # Пробуем получить из кэша
    cached_data = MongoCacheHelper.get_cached_favourite_posts(
        request.user.id, scientific_field_id, post_type
    )

    if cached_data:
        print("✅ Избранные посты получены из кэша MongoDB")
        return render(request, 'posts/favourite_posts.html', cached_data)

    print("🔄 Избранные посты загружаются из базы данных")

    # Получаем избранные посты
    favourite_posts = Post.objects.filter(favourited_by__user=request.user).annotate(
        like_count=Count('post_likes'),
        comment_count=Count('comments'),
        favourite_count=Count('favourited_by')
    ).order_by('-favourited_by__created_at')

    # Фильтрация
    if scientific_field_id:
        favourite_posts = favourite_posts.filter(scientific_field_id=scientific_field_id)
    if post_type:
        favourite_posts = favourite_posts.filter(post_type=post_type)

    scientific_fields = ScientificField.objects.all()

    context = {
        'posts': favourite_posts,
        'scientific_fields': scientific_fields,
        'current_field': scientific_field_id,
        'current_post_type': post_type,
        'cache_timestamp': time.time()
    }

    # Сохраняем в кэш
    MongoCacheHelper.cache_favourite_posts(
        request.user.id, scientific_field_id, post_type, context
    )

    return render(request, 'posts/favourite_posts.html', context)


@login_required
def post_detail(request, post_id):
    """Детальная страница поста"""
    # Пробуем получить из кэша
    cached_data = MongoCacheHelper.get_cached_post_detail(post_id)

    if cached_data:
        print("✅ Детали поста получены из кэша MongoDB")
        # Добавляем форму комментария (не кэшируется)
        cached_data['comment_form'] = CommentForm()
        return render(request, 'posts/post_detail.html', cached_data)

    print("🔄 Детали поста загружаются из базы данных")

    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.all().order_by('created_at')

    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()

            # Инвалидируем кэш поста при добавлении комментария
            MongoCacheHelper.invalidate_post_cache(post_id)

            messages.success(request, "Комментарий добавлен!")
            return redirect('posts:post_detail', post_id=post.id)
    else:
        comment_form = CommentForm()

    context = {
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
        'cache_timestamp': time.time()
    }

    # Сохраняем в кэш (без формы)
    cache_context = context.copy()
    cache_context.pop('comment_form', None)  # Убираем форму из кэша
    MongoCacheHelper.cache_post_detail(post_id, cache_context)

    return render(request, 'posts/post_detail.html', context)


@login_required
def like_post(request, post_id):
    """Лайк/анлайк поста"""
    post = get_object_or_404(Post, id=post_id)
    like, created = PostLike.objects.get_or_create(
        user=request.user,
        post=post
    )

    # Инвалидируем кэш поста
    MongoCacheHelper.invalidate_post_cache(post_id)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if not created:
            like.delete()
            return JsonResponse({
                'liked': False,
                'like_count': post.post_likes.count()
            })
        return JsonResponse({
            'liked': True,
            'like_count': post.post_likes.count()
        })

    if not created:
        like.delete()
        messages.info(request, "Лайк удален")
    else:
        messages.success(request, "Пост лайкнут")

    return redirect(request.META.get('HTTP_REFERER', 'posts:news_feed'))


@login_required
def delete_post(request, post_id):
    """Удаление поста"""
    post = get_object_or_404(Post, id=post_id)

    if post.author != request.user:
        messages.error(request, "Вы можете удалять только свои посты")
        return redirect('posts:news_feed')

    if request.method == 'POST':
        # Инвалидируем кэш перед удалением
        MongoCacheHelper.invalidate_post_cache(post_id)
        MongoCacheHelper.invalidate_user_cache(request.user.id)

        post.delete()
        messages.success(request, "Пост успешно удален")
        return redirect('posts:news_feed')

    context = {
        'post': post,
    }
    return render(request, 'posts/confirm_delete.html', context)