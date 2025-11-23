from django import forms
from django.conf import settings  # Добавляем импорт settings
from .models import Chat, Message
from users.models import User  # Добавляем импорт User


class ChatForm(forms.ModelForm):
    class Meta:
        model = Chat
        fields = ['name']  # Убираем chat_type, так как теперь только групповые чаты
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название группового чата'
            }),
        }
        labels = {
            'name': 'Название чата',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True  # Для групповых чатов название обязательно


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Введите сообщение...'
            }),
        }
        labels = {
            'content': '',
        }


class AddMembersForm(forms.Form):
    users = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        label="Добавить участников"
    )

    def __init__(self, *args, **kwargs):
        current_chat = kwargs.pop('current_chat', None)
        super().__init__(*args, **kwargs)
        if current_chat:
            # Исключаем уже добавленных пользователей
            existing_members = current_chat.members.all()
            self.fields['users'].queryset = User.objects.exclude(
                id__in=existing_members.values_list('id', flat=True)
            )