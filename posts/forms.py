from django import forms
from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'post_type', 'scientific_field']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Поделитесь своими мыслями, исследованиями или задайте вопрос...'
            }),
            'title': forms.TextInput(attrs={
                'placeholder': 'Заголовок публикации'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].label = "Заголовок"
        self.fields['content'].label = "Содержание"
        self.fields['post_type'].label = "Тип публикации"
        self.fields['scientific_field'].label = "Научная область"

        # Делаем поле научной области необязательным
        self.fields['scientific_field'].required = False


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Напишите комментарий...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['content'].label = ""