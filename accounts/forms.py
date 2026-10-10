import re
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import AuthenticationForm


class RegisterForm(forms.Form):
    username = forms.CharField(
        label="Kullanıcı Adı",
        min_length=3,
        max_length=20,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "kullanici_adi",
                "autocomplete": "username",
                "autofocus": True,
            }
        ),
        help_text="3–20 karakter, sadece harf, rakam ve alt çizgi (_).",
    )
    email = forms.EmailField(
        label="E-posta Adresi",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "ornek@alanadi.com",
                "autocomplete": "email",
            }
        ),
        help_text="E-posta adresin diğer kullanıcılara asla gösterilmez.",
    )
    password = forms.CharField(
        label="Parola",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "En az 8 karakter",
                "autocomplete": "new-password",
            }
        ),
    )
    password_confirm = forms.CharField(
        label="Parola Tekrarı",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Parolanı tekrar gir",
                "autocomplete": "new-password",
            }
        ),
    )

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()
        if not re.match(r"^[a-zA-Z0-9_]{3,20}$", username):
            raise ValidationError(
                "Kullanıcı adı 3-20 karakter olmalı ve yalnızca harf, rakam ve alt çizgi içermelidir."
            )
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("Bu kullanıcı adı zaten alınmış. Farklı bir kullanıcı adı seç.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Bu e-posta adresiyle kayıtlı bir hesap zaten var.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm:
            if password != password_confirm:
                self.add_error("password_confirm", "Girdiğin parolalar birbiriyle eşleşmiyor.")
            else:
                try:
                    validate_password(password)
                except ValidationError as e:
                    self.add_error("password", e)
        return cleaned_data

    def save(self):
        username = self.cleaned_data["username"]
        email = self.cleaned_data["email"]
        password = self.cleaned_data["password"]
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
        )
        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Kullanıcı Adı",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Kullanıcı adın",
                "autocomplete": "username",
                "autofocus": True,
            }
        ),
    )
    password = forms.CharField(
        label="Parola",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Parolan",
                "autocomplete": "current-password",
            }
        ),
    )

    error_messages = {
        "invalid_login": "Kullanıcı adı veya parola hatalı. Lütfen kontrol edip tekrar dene.",
        "inactive": "Bu hesap devre dışı bırakılmış.",
    }
