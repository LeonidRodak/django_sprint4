from django import forms
from django.contrib.auth.models import User
from .models import Post, Comment


class ProfileEditForm(forms.ModelForm):
    # Указываем какую модель и какие поля используем
    class Meta:
        model = User
        # только эти поля можно редактировать
        fields = ('first_name', 'last_name', 'username', 'email')


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('title', 'text', 'pub_date', 'location', 'category', 'image')
        widgets = {
            # Настраиваем виджет для поля даты/времени публикации
            'pub_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
