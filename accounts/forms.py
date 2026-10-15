from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import re

class StudentRegistrationForm(forms.Form):
    full_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Jane Doe',
            'id': 'regFullName',
            'autofocus': 'autofocus'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'jane.doe@university.edu',
            'id': 'regEmail'
        })
    )
    password = forms.CharField(
        min_length=6,
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'At least 6 characters',
            'id': 'regPassword'
        })
    )
    confirm_password = forms.CharField(
        min_length=6,
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Repeat your password',
            'id': 'regConfirmPassword'
        })
    )

    def clean_full_name(self):
        name = self.cleaned_data.get('full_name', '').strip()
        if len(name) < 2:
            raise ValidationError("Full name must be at least 2 characters long.")
        return name

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exists() or User.objects.filter(username__iexact=email).exists():
            raise ValidationError("An account with this email address already exists. Please log in.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        pw = cleaned_data.get('password')
        confirm_pw = cleaned_data.get('confirm_password')

        if pw and confirm_pw and pw != confirm_pw:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data

    def save(self):
        full_name = self.cleaned_data['full_name']
        email = self.cleaned_data['email']
        password = self.cleaned_data['password']

        parts = full_name.split(' ', 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ''

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        return user

class StudentLoginForm(forms.Form):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'name@domain.edu',
            'id': 'loginEmail',
            'autofocus': 'autofocus'
        })
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••',
            'id': 'loginPassword'
        })
    )
