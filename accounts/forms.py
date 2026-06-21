from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import Profile


class StyledFormMixin:
    def _apply_field_styles(self):
        for field in self.fields.values():
            widget = field.widget
            base = widget.attrs.get("class", "")
            widget.attrs["class"] = (base + " form-input").strip()


class RegisterForm(StyledFormMixin, UserCreationForm):
    first_name = forms.CharField(label="Ism", max_length=80, required=False)
    last_name = forms.CharField(label="Familiya", max_length=80, required=False)
    email = forms.EmailField(label="Email", required=False)
    phone = forms.CharField(label="Telefon", max_length=32, required=False)

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "phone", "password1", "password2")
        labels = {
            "username": "Username",
        }
        widgets = {
            "username": forms.TextInput(attrs={"placeholder": "Masalan: ali_reader"}),
            "first_name": forms.TextInput(attrs={"placeholder": "Ismingiz"}),
            "last_name": forms.TextInput(attrs={"placeholder": "Familiyangiz"}),
            "email": forms.EmailInput(attrs={"placeholder": "email@example.com"}),
            "phone": forms.TextInput(attrs={"placeholder": "+998 ..."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget.attrs.update({"placeholder": "Kamida 8 belgili kuchli parol"})
        self.fields["password2"].widget.attrs.update({"placeholder": "Parolni qayta kiriting"})
        for field in self.fields.values():
            field.help_text = ""
        self._apply_field_styles()

    def save(self, commit=True):
        phone = self.cleaned_data.pop("phone", "")
        user = super().save(commit=commit)
        if commit:
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.phone = phone
            profile.save(update_fields=["phone", "updated_at"])
        return user


class LoginForm(StyledFormMixin, AuthenticationForm):
    username = forms.CharField(
        label="Username",
        widget=forms.TextInput(attrs={"placeholder": "Username yoki login"}),
    )
    password = forms.CharField(
        label="Parol",
        widget=forms.PasswordInput(attrs={"placeholder": "Parolingiz"}),
    )

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        self._apply_field_styles()


class UserUpdateForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
        labels = {
            "first_name": "Ism",
            "last_name": "Familiya",
            "email": "Email",
        }
        widgets = {
            "first_name": forms.TextInput(attrs={"placeholder": "Ismingiz"}),
            "last_name": forms.TextInput(attrs={"placeholder": "Familiyangiz"}),
            "email": forms.EmailInput(attrs={"placeholder": "email@example.com"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_field_styles()


class ProfileUpdateForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("display_name", "phone", "bio", "avatar")
        widgets = {
            "display_name": forms.TextInput(attrs={"placeholder": "Profil nomi"}),
            "phone": forms.TextInput(attrs={"placeholder": "+998 ..."}),
            "bio": forms.Textarea(attrs={"rows": 4, "placeholder": "O'zingiz haqida qisqacha"}),
            "avatar": forms.FileInput(attrs={"accept": "image/*"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_field_styles()
