from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Profile, ScientificField


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email")
    first_name = forms.CharField(max_length=30, required=True, label="Имя")
    last_name = forms.CharField(max_length=30, required=True, label="Фамилия")

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'is_researcher']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Делаем поля красивыми
        self.fields['username'].label = "Имя пользователя"
        self.fields['password1'].label = "Пароль"
        self.fields['password2'].label = "Подтверждение пароля"
        self.fields['is_researcher'].label = "Я исследователь"


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(label="Имя пользователя или Email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password'].widget.attrs.update({'class': 'form-control'})


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            'avatar', 'bio', 'scientific_fields', 'institution', 'website',
            'phone', 'location', 'research_interests', 'education', 'academic_degree',
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Расскажите о себе...'}),
            'research_interests': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Ваши научные интересы...'}),
            'education': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Ваше образование...'}),
            'scientific_fields': forms.SelectMultiple(attrs={'class': 'form-control', 'size': '5'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['bio'].label = "Биография"
        self.fields['scientific_fields'].label = "Научные области"
        self.fields['institution'].label = "Учреждение"
        self.fields['website'].label = "Веб-сайт"
        self.fields['avatar'].label = "Аватар"
        self.fields['phone'].label = "Телефон"
        self.fields['location'].label = "Местоположение"
        self.fields['research_interests'].label = "Научные интересы (подробно)"
        self.fields['education'].label = "Образование"
        self.fields['academic_degree'].label = "Ученая степень"

        # Делаем поля необязательными
        for field in self.fields:
            self.fields[field].required = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['bio'].label = "Биография"
        self.fields['scientific_fields'].label = "Научные интересы"
        self.fields['institution'].label = "Учреждение"
        self.fields['website'].label = "Веб-сайт"
        self.fields['avatar'].label = "Аватар"
        self.fields['phone'].label = "Телефон"
        self.fields['location'].label = "Местоположение"
        self.fields['research_interests'].label = "Научные интересы (подробно)"
        self.fields['education'].label = "Образование"
        self.fields['academic_degree'].label = "Ученая степень"

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'orcid_id']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].label = "Имя"
        self.fields['last_name'].label = "Фамилия"
        self.fields['email'].label = "Email"
        self.fields['orcid_id'].label = "ORCID ID"