from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from django import forms

User = get_user_model()

class LoginForm(AuthenticationForm):
    pass

class RegisterForm(UserCreationForm):
    profile_image = forms.ImageField(required=False)
    class Meta:
        model = User
        fields = ["username", "password1", "password2", "profile_image"]
