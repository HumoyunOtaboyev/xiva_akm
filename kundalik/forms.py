from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.db.models import Q

User = get_user_model()


class EmailAuthenticationForm(AuthenticationForm):
    """Kirish formasi: kitobxonlar email bilan kiradi (username = email)."""

    username = forms.CharField(
        label="Email",
        max_length=150,
        widget=forms.TextInput(attrs={"autofocus": True, "autocomplete": "email"}),
    )

    def clean_username(self):
        value = self.cleaned_data["username"].strip()
        # Emaillar kichik harfda saqlanadi; oddiy (admin) loginlar o'zgarmaydi.
        return value.lower() if "@" in value else value


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(
        label="Ismingiz",
        max_length=150,
        widget=forms.TextInput(attrs={"autocomplete": "given-name"}),
    )
    email = forms.EmailField(
        label="Email",
        max_length=150,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("first_name", "email")
        field_classes = {}

    def clean_first_name(self):
        name = self.cleaned_data["first_name"].strip()
        if not name:
            raise forms.ValidationError("Ismingizni kiriting.")
        return name

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(Q(username__iexact=email) | Q(email__iexact=email)).exists():
            raise forms.ValidationError("Bu email bilan allaqachon ro'yxatdan o'tilgan.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["email"]
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        if commit:
            user.save()
        return user
