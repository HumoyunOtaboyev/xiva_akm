from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.db.models import Q

from .models import EmailVerification

User = get_user_model()

# Django'da parol talablarining o'zbekcha tarjimasi yo'q — o'zimiz beramiz.
PASSWORD_HELP_UZ = (
    "<ul>"
    "<li>Kamida 8 ta belgi</li>"
    "<li>Faqat raqamlardan iborat bo'lmasin</li>"
    "<li>Juda oddiy (keng tarqalgan) parol bo'lmasin</li>"
    "<li>Ismingiz yoki emailingizga o'xshamasin</li>"
    "</ul>"
)
PASSWORD_ERRORS_UZ = {
    "password_too_short": "Parol juda qisqa — kamida %(min_length)d ta belgi bo'lishi kerak.",
    "password_too_common": "Bu parol juda oddiy (keng tarqalgan). Boshqasini tanlang.",
    "password_entirely_numeric": "Parol faqat raqamlardan iborat bo'lmasligi kerak.",
    "password_too_similar": "Parol ismingiz yoki emailingizga juda o'xshash.",
}
PASSWORD_MISMATCH_UZ = "Parollar bir xil emas."


def validate_password_uz(password, user=None):
    """Django parol tekshiruvlari, xabarlari o'zbekcha."""
    try:
        password_validation.validate_password(password, user)
    except forms.ValidationError as exc:
        errors = []
        for err in exc.error_list:
            message = PASSWORD_ERRORS_UZ.get(err.code)
            if message is None:
                errors.append(err)
            elif "%(" in message:
                errors.append(forms.ValidationError(message, code=err.code, params=err.params))
            else:
                errors.append(forms.ValidationError(message, code=err.code))
        raise forms.ValidationError(errors)


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
    error_messages = {**UserCreationForm.error_messages, "password_mismatch": PASSWORD_MISMATCH_UZ}

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].label = "Parol"
        self.fields["password1"].help_text = PASSWORD_HELP_UZ
        self.fields["password2"].label = "Parolni takrorlang"
        self.fields["password2"].help_text = ""

    def _post_clean(self):
        # UserCreationForm._post_clean o'rniga: xabarlar o'zbekcha bo'lishi uchun.
        forms.ModelForm._post_clean(self)
        password = self.cleaned_data.get("password2")
        if password:
            try:
                validate_password_uz(password, self.instance)
            except forms.ValidationError as error:
                self.add_error("password2", error)

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


def code_field():
    return forms.CharField(
        label="Emailga kelgan kod",
        max_length=12,
        widget=forms.TextInput(attrs={
            "autocomplete": "one-time-code",
            "inputmode": "numeric",
            "autofocus": True,
            "placeholder": "••••••",
            "class": "code-input",
        }),
    )


def clean_code_value(value):
    code = "".join(ch for ch in value if ch.isdigit())
    if len(code) != 6:
        raise forms.ValidationError("6 xonali kodni kiriting.")
    return code


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        max_length=150,
        widget=forms.EmailInput(attrs={"autocomplete": "email", "autofocus": True}),
    )

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()


class PasswordResetConfirmForm(forms.Form):
    code = code_field()
    new_password1 = forms.CharField(
        label="Yangi parol",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text=PASSWORD_HELP_UZ,
    )
    new_password2 = forms.CharField(
        label="Yangi parolni takrorlang",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_code(self):
        return clean_code_value(self.cleaned_data["code"])

    def clean_new_password2(self):
        p1 = self.cleaned_data.get("new_password1")
        p2 = self.cleaned_data["new_password2"]
        if p1 and p1 != p2:
            raise forms.ValidationError(PASSWORD_MISMATCH_UZ)
        validate_password_uz(p2, self.user)
        return p2


class VerifyCodeForm(forms.Form):
    code = code_field()

    def clean_code(self):
        return clean_code_value(self.cleaned_data["code"])
