from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError

from .models import Profile

User = get_user_model()

class AskForm(forms.Form):
    title = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "maxlength": "255",
            "placeholder": "How to build a moon park ?",
        })
    )
    text = forms.CharField(
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 6,
            "placeholder": "Really, how? Have no idea about it",
        })
    )
    tags = forms.CharField(
        help_text="Tags separated by space or comma",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "moon, park, puzzle",
        })
    )

    def clean_tags(self):
        raw = self.cleaned_data["tags"].replace(",", " ")
        tags = [t.strip().lower() for t in raw.split() if t.strip()]
        if not tags:
            raise forms.ValidationError("At least one tag is required.")
        if len(tags) > 3:
            raise forms.ValidationError("No more than 3 tags.")
        return tags


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter your login here",
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Enter your password",
        })
    )

    def clean(self):
        cleaned = super().clean()
        user = authenticate(
            username=cleaned.get("username"),
            password=cleaned.get("password"),
        )
        if user is None:
            raise ValidationError("Wrong login or password")
        self.user = user
        return cleaned


class SignupForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "dr_pepper",
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "drpepper@mail.ru",
        })
    )
    nick = forms.CharField(
        max_length=64,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Dr. Pepper",
        })
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Enter password",
        })
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Repeat password",
        })
    )
    avatar = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={"class": "form-control"})
    )

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username=username).exists():
            raise ValidationError("This login is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise ValidationError("Sorry, this email address already registered!")
        return email

    def clean_nick(self):
        nick = self.cleaned_data["nick"]
        if Profile.objects.filter(nick=nick).exists():
            raise ValidationError("This nickname is already taken.")
        return nick

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password1") != cleaned.get("password2"):
            raise ValidationError("Passwords do not match.")
        return cleaned

    def save(self):
        user = User.objects.create_user(
            username=self.cleaned_data["username"],
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password1"],
        )
        profile = user.profile
        profile.nick = self.cleaned_data["nick"]
        if self.cleaned_data.get("avatar") is not None:
            profile.avatar = self.cleaned_data["avatar"]
        profile.save()
        return user


class ProfileEditForm(forms.Form):
    email = forms.EmailField(label="Email")
    nick = forms.CharField(max_length=64, label="Nick")
    avatar = forms.ImageField(required=False, label="Avatar")

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_nick(self):
        nick = self.cleaned_data["nick"]
        qs = Profile.objects.filter(nick=nick).exclude(user=self.user)
        if qs.exists():
            raise ValidationError("Такой nick уже занят")
        return nick

    def save(self):
        self.user.email = self.cleaned_data["email"]
        self.user.save()

        profile = self.user.profile
        profile.nick = self.cleaned_data["nick"]
        if self.cleaned_data.get("avatar") is not None:
            profile.avatar = self.cleaned_data["avatar"]
        profile.save()
        return profile

class AnswerForm(forms.Form):
    text = forms.CharField(
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 4,
            "placeholder": "Enter your answer here.",
        })
    )