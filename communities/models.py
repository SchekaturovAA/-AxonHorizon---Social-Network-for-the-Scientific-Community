from django.db import models
from django.conf import settings
from django.urls import reverse

class Community(models.Model):
    COMMUNITY_TYPES = (
        ('open', 'Открытое'),
        ('closed', 'Закрытое'),
        ('private', 'Приватное'),
    )

    name = models.CharField(max_length=100, unique=True, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    short_description = models.CharField(max_length=200, blank=True, verbose_name="Краткое описание")
    community_type = models.CharField(max_length=20, choices=COMMUNITY_TYPES, default='open',
                                      verbose_name="Тип сообщества")
    scientific_field = models.ForeignKey('users.ScientificField', on_delete=models.SET_NULL, null=True,
                                         related_name='communities', verbose_name="Научная область")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   related_name='created_communities', verbose_name="Создатель")
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='communities_joined',
                                     through='CommunityMembership', verbose_name="Участники")

    avatar = models.ImageField(upload_to='communities/avatars/', blank=True, null=True,
                               verbose_name="Аватар сообщества")
    banner = models.ImageField(upload_to='communities/banners/', blank=True, null=True,
                               verbose_name="Баннер сообщества")

    rules = models.TextField(blank=True, verbose_name="Правила сообщества")
    website = models.URLField(blank=True, verbose_name="Веб-сайт")
    contact_email = models.EmailField(blank=True, verbose_name="Контактный email")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Сообщество"
        verbose_name_plural = "Сообщества"
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def member_count(self):
        return self.members.count()

    def post_count(self):
        return self.posts.count()

    def is_creator(self, user):
        return self.created_by == user

    def is_moderator(self, user):
        # ЗАМЕНА: используем filter().first() вместо get() для обработки дубликатов
        membership = CommunityMembership.objects.filter(user=user, community=self).first()
        if membership:
            return membership.is_moderator
        return False

    def is_member(self, user):
        return self.members.filter(id=user.id).exists()


class CommunityMembership(models.Model):
    ROLE_CHOICES = (
        ('member', 'Участник'),
        ('moderator', 'Модератор'),
        ('admin', 'Администратор'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Пользователь")
    community = models.ForeignKey(Community, on_delete=models.CASCADE, verbose_name="Сообщество")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member', verbose_name="Роль")
    date_joined = models.DateTimeField(auto_now_add=True, verbose_name="Дата вступления")
    is_moderator = models.BooleanField(default=False, verbose_name="Модератор")

    class Meta:
        verbose_name = "Участник сообщества"
        verbose_name_plural = "Участники сообществ"
        unique_together = ('user', 'community')  # Это должно предотвращать дубликаты

    def __str__(self):
        return f"{self.user} в {self.community} ({self.role})"

    def save(self, *args, **kwargs):
        # Синхронизируем is_moderator с ролью
        self.is_moderator = self.role in ['moderator', 'admin']
        super().save(*args, **kwargs)