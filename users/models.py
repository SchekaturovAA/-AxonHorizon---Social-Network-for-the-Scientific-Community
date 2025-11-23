from django.contrib.auth.models import AbstractUser
from django.db import models


class ScientificField(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Научная область"
        verbose_name_plural = "Научные области"

    def __str__(self):
        return self.name


class User(AbstractUser):
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='Группы',
        blank=True,
        help_text='Группы, к которым принадлежит пользователь.',
        related_name='axonhorizon_user_set',
        related_query_name='axonhorizon_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='Права пользователя',
        blank=True,
        help_text='Конкретные права для этого пользователя.',
        related_name='axonhorizon_user_set',
        related_query_name='axonhorizon_user',
    )

    is_researcher = models.BooleanField(default=False, verbose_name="Исследователь")
    is_verified = models.BooleanField(default=False, verbose_name="Подтвержден")
    orcid_id = models.CharField(max_length=19, blank=True, null=True, unique=True, verbose_name="ORCID ID")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата регистрации")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def get_unread_chats_count(self):
        """Количество чатов с непрочитанными сообщениями"""
        from chats.models import Chat, ChatMember, Message
        user_chats = Chat.objects.filter(members=self)
        unread_count = 0

        for chat in user_chats:
            try:
                chat_member = ChatMember.objects.get(chat=chat, user=self)
                unread_messages = Message.objects.filter(
                    chat=chat,
                    created_at__gt=chat_member.last_read
                ).count()
                if unread_messages > 0:
                    unread_count += 1
            except ChatMember.DoesNotExist:
                continue

        return unread_count

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.username

    def get_friends(self):
        """Получить список принятых друзей"""
        # Друзья, которые приняли наши запросы
        sent_accepted = User.objects.filter(
            friendship_requests_received__from_user=self,
            friendship_requests_received__status='accepted'
        )
        # Друзья, чьи запросы мы приняли
        received_accepted = User.objects.filter(
            friendship_requests_sent__to_user=self,
            friendship_requests_sent__status='accepted'
        )
        return (sent_accepted | received_accepted).distinct()

    def get_pending_requests(self):
        """Получить входящие запросы дружбы"""
        return self.friendship_requests_received.filter(status='pending')

    def get_sent_requests(self):
        """Получить исходящие запросы дружбы"""
        return self.friendship_requests_sent.filter(status='pending')

    def get_friends_count(self):
        """Количество друзей"""
        return self.get_friends().count()

    def is_friends_with(self, user):
        """Проверить, друзья ли с пользователем"""
        if not user.is_authenticated:
            return False
        return Friendship.objects.filter(
            models.Q(from_user=self, to_user=user, status='accepted') |
            models.Q(from_user=user, to_user=self, status='accepted')
        ).exists()

    def has_pending_request_from(self, user):
        """Есть ли pending запрос от пользователя"""
        return self.friendship_requests_received.filter(
            from_user=user, status='pending'
        ).exists()

    def has_pending_request_to(self, user):
        """Отправлен ли pending запрос пользователю"""
        return self.friendship_requests_sent.filter(
            to_user=user, status='pending'
        ).exists()


class Profile(models.Model):
    user = models.OneToOneField('User', on_delete=models.CASCADE, related_name='profile', verbose_name="Пользователь")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="Аватар")
    bio = models.TextField(max_length=500, blank=True, verbose_name="Биография")
    scientific_fields = models.ManyToManyField(ScientificField, related_name='profiles', blank=True,
                                               verbose_name="Научные области")
    citations_count = models.IntegerField(default=0, verbose_name="Количество цитирований")
    h_index = models.IntegerField(default=0, verbose_name="Индекс Хирша")
    institution = models.CharField(max_length=255, blank=True, verbose_name="Учреждение")
    website = models.URLField(blank=True, verbose_name="Веб-сайт")
    phone = models.CharField(max_length=12, blank=True, verbose_name="Телефон")
    location = models.CharField(max_length=100, blank=True, verbose_name="Местоположение")
    research_interests = models.TextField(max_length=800, blank=True, verbose_name="Научные интересы")
    education = models.TextField(max_length=150, blank=True, verbose_name="Образование")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    ACADEMIC_DEGREE_CHOICES = (
        ('bachelor', 'Бакалавр'),
        ('master', 'Магистр'),
        ('candidate', 'Кандидат наук'),
        ('doctor', 'Доктор наук'),
        ('professor', 'Профессор'),
    )

    academic_degree = models.CharField(
        max_length=20,
        choices=ACADEMIC_DEGREE_CHOICES,
        default='none',
        blank=True,
        verbose_name="Ученая степень"
    )
    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"

    def __str__(self):
        return f"Профиль {self.user.username}"


class Friendship(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Ожидание'),
        ('accepted', 'Принято'),
        ('rejected', 'Отклонено'),
    )

    from_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='friendship_requests_sent',
        verbose_name="От пользователя"
    )
    to_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='friendship_requests_received',
        verbose_name="К пользователю"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Статус"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Запрос дружбы"
        verbose_name_plural = "Запросы дружбы"
        unique_together = ('from_user', 'to_user')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.from_user} → {self.to_user} ({self.status})"

    def accept(self):
        """Принять запрос дружбы"""
        self.status = 'accepted'
        self.save()

    def reject(self):
        """Отклонить запрос дружбы"""
        self.status = 'rejected'
        self.save()


# Пользователи: admin/admin; user1/1234567890AA; user2/1234567DD; user3/123456789XX