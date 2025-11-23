from django.db import models
from django.conf import settings
from django.utils import timezone


class Chat(models.Model):
    CHAT_TYPES = (
        ('personal', 'Личный чат'),
        ('group', 'Групповой чат'),
    )

    name = models.CharField(max_length=255, blank=True, verbose_name="Название чата")
    chat_type = models.CharField(max_length=20, choices=CHAT_TYPES, default='personal', verbose_name="Тип чата")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   related_name='created_chats', verbose_name="Создатель")
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, through='ChatMember',
                                     related_name='chats', verbose_name="Участники")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Чат"
        verbose_name_plural = "Чаты"
        ordering = ['-updated_at']

    def __str__(self):
        if self.chat_type == 'personal':
            members = self.members.exclude(id=self.created_by_id)
            if members.exists():
                return f"Чат с {members.first().get_full_name()}"
        return self.name or f"Чат {self.id}"

    def get_last_message(self):
        return self.messages.order_by('-created_at').first()

    def get_unread_count(self, user):
        return self.messages.filter(created_at__gt=user.chat_members.get(chat=self).last_read).count()


class ChatMember(models.Model):
    ROLE_CHOICES = (
        ('member', 'Участник'),
        ('admin', 'Администратор'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Пользователь")
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, verbose_name="Чат")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member', verbose_name="Роль")
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата вступления")
    last_read = models.DateTimeField(default=timezone.now, verbose_name="Последнее прочтение")

    class Meta:
        verbose_name = "Участник чата"
        verbose_name_plural = "Участники чатов"
        unique_together = ('user', 'chat')

    def __str__(self):
        return f"{self.user} в {self.chat}"


class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages', verbose_name="Чат")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               related_name='messages', verbose_name="Автор")
    content = models.TextField(verbose_name="Содержание")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    read_by = models.ManyToManyField(settings.AUTH_USER_MODEL, through='MessageRead',
                                     related_name='read_messages', verbose_name="Прочитано")

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        ordering = ['created_at']

    def __str__(self):
        return f"Сообщение от {self.author} в {self.chat}"


class MessageRead(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Пользователь")
    message = models.ForeignKey(Message, on_delete=models.CASCADE, verbose_name="Сообщение")
    read_at = models.DateTimeField(auto_now_add=True, verbose_name="Время прочтения")

    class Meta:
        verbose_name = "Прочитанное сообщение"
        verbose_name_plural = "Прочитанные сообщения"
        unique_together = ('user', 'message')