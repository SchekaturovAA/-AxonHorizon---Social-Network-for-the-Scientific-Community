from django.db import models
from django.conf import settings


class Post(models.Model):
    POST_TYPES = (
        ('article', 'Исследовательская статья'),
        ('preprint', 'Препринт'),
        ('question', 'Вопрос'),
        ('discussion', 'Обсуждение'),
        ('news', 'Новость'),
    )

    title = models.CharField(max_length=255, verbose_name="Заголовок")
    content = models.TextField(verbose_name="Содержание")
    post_type = models.CharField(max_length=20, choices=POST_TYPES, default='discussion', verbose_name="Тип публикации")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts',
                               verbose_name="Автор")
    scientific_field = models.ForeignKey('users.ScientificField', on_delete=models.SET_NULL, null=True, blank=True,
                                         related_name='posts', verbose_name="Научная область")
    community = models.ForeignKey('communities.Community', on_delete=models.CASCADE, null=True, blank=True,
                                  related_name='posts', verbose_name="Сообщество")
    doi = models.CharField(max_length=100, blank=True, null=True, verbose_name="DOI")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Публикация"
        verbose_name_plural = "Публикации"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def like_count(self):
        """Количество лайков у поста"""
        return self.post_likes.count()

    def comment_count(self):
        """Количество комментариев у поста"""
        return self.comments.count()


class PostLike(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Пользователь")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_likes', verbose_name="Публикация")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Лайк"
        verbose_name_plural = "Лайки"
        unique_together = ('user', 'post')

    def __str__(self):
        return f"Лайк от {self.user} на {self.post}"


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments', verbose_name="Публикация")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='post_comments',
                               verbose_name="Автор")
    content = models.TextField(verbose_name="Содержание")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"
        ordering = ['created_at']

    def __str__(self):
        return f"Комментарий от {self.author} к {self.post.title}"


class FavouritePost(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favourites')
    post = models.ForeignKey('Post', on_delete=models.CASCADE, related_name='favourited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'post']  # чтобы один пользователь не мог добавить пост в избранное дважды
        ordering = ['-created_at']