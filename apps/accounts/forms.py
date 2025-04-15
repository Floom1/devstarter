from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Profile


class SignUpForm(UserCreationForm):
    username = forms.CharField(max_length=30, widget=forms.TextInput(
        attrs={"class": "form-control mb-1", 'placeholder': 'Введите Ник'}))
    email = forms.EmailField(
        widget=forms.TextInput(attrs={"class": "form-control mb-1", 'placeholder': 'Введите почту'}))
    password1 = forms.CharField(max_length=50, widget=forms.PasswordInput(
        attrs={"class": "form-control mb-1", 'placeholder': 'Введите пароль'}))
    password2 = forms.CharField(max_length=50, widget=forms.PasswordInput(
        attrs={"class": "form-control mb-1", 'placeholder': 'Подтвердите пароль'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class LoginForm(AuthenticationForm):
    username = forms.CharField(max_length=100,
                               required=True,
                               widget=forms.TextInput(attrs={"class": "form-control mb-1", 'placeholder': 'Ник'}))
    password = forms.CharField(max_length=50,
                               required=True,
                               widget=forms.PasswordInput(attrs={"class": "form-control mb-1", 'placeholder': 'Пароль'}))
    remember_me = forms.BooleanField(required=False)

    class Meta:
        model = User
        field = ['username', 'password', 'remember_me']



class UserUpdateForm(forms.ModelForm):
    class_css = {"class": "form-control mb-1"}
    username = forms.CharField(max_length=100, widget=forms.TextInput(
        attrs=class_css
    ))
    email = forms.EmailField(widget=forms.TextInput(attrs=
            class_css))

    class Meta:
        model = User
        fields = ('username', 'email')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Email адрес должен быть уникальнм')
        return email


class ProfileUpdateForm(forms.ModelForm):
    class_css = {"class": "form-control mb-1"}
    birth_date = forms.DateField(
        widget=forms.TextInput(attrs=class_css)
    )
    bio = forms.CharField(max_length=500,
                          widget=forms.Textarea(attrs={"rows": 5, "class": "form-control mb-1"}))
    avatar = forms.ImageField(widget=forms.FileInput(attrs=class_css))

    class Meta:
        model = Profile
        fields = ('birth_date', 'bio', 'avatar')