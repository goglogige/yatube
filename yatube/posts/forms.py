from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['group', 'text', 'image']
        labels = {
            'group': _('Группа'),
            'text': _('Текст'),
            'image': _('Изображение'),
        }
        help_texts = {
            'group': _('Выберите группу для публикации'),
            'text': _('Введите текст публикации'),
            'image': _('Выберите изображение для публикации'),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {'text': forms.Textarea(attrs={'cols': 100, 'rows': 5})}
        labels = {
            'text': _('Текст'),
        }
        help_texts = {
            'text': _('Введите текст комментария'),
        }


