from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, AccountRequest


class StudentForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username']
        help_texts = {'username': None}


class AccountRequestForm(forms.ModelForm):
    class Meta:
        model = AccountRequest
        fields = ['full_name', 'reason']
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Why do you want to be a teacher?'}),
        }
