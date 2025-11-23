from django import forms
from .models import Community, CommunityMembership


class CommunityForm(forms.ModelForm):
    class Meta:
        model = Community
        fields = [
            'name', 'short_description', 'description', 'community_type',
            'scientific_field', 'avatar', 'banner', 'rules',
            'website', 'contact_email'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Подробное описание сообщества...'}),
            'short_description': forms.TextInput(attrs={'placeholder': 'Краткое описание (до 200 символов)...'}),
            'rules': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Правила сообщества...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].label = "Название сообщества"
        self.fields['short_description'].label = "Краткое описание"
        self.fields['description'].label = "Полное описание"
        self.fields['community_type'].label = "Тип сообщества"
        self.fields['scientific_field'].label = "Научная область"
        self.fields['avatar'].label = "Аватар сообщества"
        self.fields['banner'].label = "Баннер сообщества"
        self.fields['rules'].label = "Правила сообщества"
        self.fields['website'].label = "Веб-сайт"
        self.fields['contact_email'].label = "Контактный email"


class CommunitySettingsForm(forms.ModelForm):
    class Meta:
        model = Community
        fields = ['description', 'community_type', 'rules', 'website', 'contact_email']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'rules': forms.Textarea(attrs={'rows': 3}),
        }


class RoleChangeForm(forms.ModelForm):
    class Meta:
        model = CommunityMembership
        fields = ['role']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].label = "Роль участника"