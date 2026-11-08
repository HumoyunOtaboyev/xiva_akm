from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.db.models import Q

from .models import EmailVerification

User = get_user_model()


class EmailAuthenticationForm(AuthenticationForm):
    """Kirish formasi: kitobxonlar email bilan kiradi (username = email)."""

    username = forms.CharField(
        label="Email",
        max_length=150,
        widget=forms.TextInput(attrs={"autofocus": True, "autocomplete": "email"}),
    )

    pending_user = None  # email tasdiqlanmagan, lekin parol to'g'ri kiritilgan foydalanuvchi

    def clean_username(self):
        value = self.cleaned_data["username"].strip()
        # Emaillar kichik harfda saqlanadi; oddiy (admin) loginlar o'zgarmaydi.
        return value.lower() if "@" in value else value

    def clean(self):
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")
        if username and password:
            user = User.objects.filter(username=username).first()
            if (
                user is not None
                and EmailVerification.is_pending(user)
                and user.check_password(password)
            ):
                # View kodni qayta yuborib, tasdiqlash sahifasiga yo'naltiradi.
                self.pending_user = user
                return self.cleaned_data
        return super().clean()


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

    existing_user = None  # emailini tasdiqlamay qolgan avvalgi ro'yxat

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        existing = User.objects.filter(Q(username__iexact=email) | Q(email__iexact=email)).first()
        if existing is not None:
            if EmailVerification.is_pending(existing):
                # Tasdiqlanmagan ro'yxatni qayta yozishga ruxsat beramiz: aks holda
                # boshqa odam emailingizni "band qilib" qo'yishi mumkin edi.
                self.existing_user = existing
            else:
                raise forms.ValidationError("Bu email bilan allaqachon ro'yxatdan o'tilgan.")
        return email

    def save(self, commit=True):
        """Foydalanuvchi email tasdiqlanguncha faol emas (is_active=False)."""
        if self.existing_user is not None:
            user = self.existing_user
            user.set_password(self.cleaned_data["password1"])
        else:
            user = super().save(commit=False)
        user.username = self.cleaned_data["email"]
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.is_active = False
        if commit:
            user.save()
        return user


class VerifyCodeForm(forms.Form):
    code = forms.CharField(
        label="Tasdiqlash kodi",
        max_length=12,
        widget=forms.TextInput(attrs={
            "autocomplete": "one-time-code",
            "inputmode": "numeric",
            "autofocus": True,
            "placeholder": "••••••",
            "class": "code-input",
        }),
    )

    def clean_code(self):
        code = "".join(ch for ch in self.cleaned_data["code"] if ch.isdigit())
        if len(code) != 6:
            raise forms.ValidationError("6 xonali kodni kiriting.")
        return code
