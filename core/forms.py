from __future__ import annotations

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Skill, SwapRequest, User

# Domains that are almost always typos of gmail.com (not valid Gmail addresses).
_GMAIL_LIKELY_TYPOS = {
    "gmai.com": "gmail.com",
    "gmial.com": "gmail.com",
    "gmal.com": "gmail.com",
    "gamil.com": "gmail.com",
    "gnail.com": "gmail.com",
    "gmaill.com": "gmail.com",
    "gmail.co": "gmail.com",
    "gmail.cmo": "gmail.com",
    "gmail.con": "gmail.com",
    "gmail.om": "gmail.com",
}


def _suggest_email_if_gmail_typo(email: str) -> str | None:
    """If the domain looks like a mistyped gmail.com, return a suggested address."""
    parts = email.rsplit("@", 1)
    if len(parts) != 2:
        return None
    local, domain = parts
    fix = _GMAIL_LIKELY_TYPOS.get(domain.lower())
    if fix:
        return f"{local}@{fix}"
    return None


def _apply_form_control_styling(form: forms.Form) -> None:
    for field in form.fields.values():
        widget = field.widget
        existing = widget.attrs.get("class", "")
        widget.attrs["class"] = (existing + " form-control").strip()
        if isinstance(widget, forms.PasswordInput):
            widget.attrs.setdefault("placeholder", "••••••••")


class RegisterForm(UserCreationForm):
    full_name = forms.CharField(max_length=150, label="Name")
    email = forms.EmailField()

    offered_skill_name = forms.CharField(max_length=100, required=False, label="Skill offered (optional)")
    offered_skill_level = forms.ChoiceField(choices=Skill.Level.choices, required=False, label="Offered skill level")

    wanted_skill_name = forms.CharField(max_length=100, required=False, label="Skill wanted (optional)")
    wanted_skill_level = forms.ChoiceField(choices=Skill.Level.choices, required=False, label="Wanted skill level")

    class Meta:
        model = User
        fields = ("full_name", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_form_control_styling(self)

        self.fields["full_name"].widget.attrs.setdefault("placeholder", "Your name")
        self.fields["email"].widget.attrs.setdefault("placeholder", "you@example.com")
        self.fields["offered_skill_name"].widget.attrs.setdefault("placeholder", "e.g., Python, Cooking")
        self.fields["wanted_skill_name"].widget.attrs.setdefault("placeholder", "e.g., Guitar, UI Design")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        suggestion = _suggest_email_if_gmail_typo(email)
        if suggestion:
            raise forms.ValidationError(
                f"The domain looks like a typo. Did you mean {suggestion}?"
            )
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user: User = super().save(commit=False)
        user.full_name = self.cleaned_data["full_name"].strip()
        user.email = self.cleaned_data["email"].strip().lower()
        user.username = user.email
        if commit:
            user.save()

            offered_name = (self.cleaned_data.get("offered_skill_name") or "").strip()
            offered_level = self.cleaned_data.get("offered_skill_level")
            if offered_name and offered_level:
                Skill.objects.create(
                    user=user,
                    skill_name=offered_name,
                    skill_level=offered_level,
                    category=Skill.Category.OFFERED,
                )

            wanted_name = (self.cleaned_data.get("wanted_skill_name") or "").strip()
            wanted_level = self.cleaned_data.get("wanted_skill_level")
            if wanted_name and wanted_level:
                Skill.objects.create(
                    user=user,
                    skill_name=wanted_name,
                    skill_level=wanted_level,
                    category=Skill.Category.WANTED,
                )

        return user


class LoginForm(AuthenticationForm):
    username = forms.EmailField(label="Email")

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request=request, *args, **kwargs)
        _apply_form_control_styling(self)
        self.fields["username"].widget.attrs.setdefault("placeholder", "you@example.com")


class ProfileForm(forms.ModelForm):
    full_name = forms.CharField(max_length=150, label="Name")

    class Meta:
        model = User
        fields = ("full_name", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_form_control_styling(self)
        self.fields["full_name"].widget.attrs.setdefault("placeholder", "Your name")
        self.fields["email"].widget.attrs.setdefault("placeholder", "you@example.com")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        suggestion = _suggest_email_if_gmail_typo(email)
        if suggestion:
            raise forms.ValidationError(
                f"The domain looks like a typo. Did you mean {suggestion}?"
            )
        qs = User.objects.filter(email=email).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("This email is already used by another account.")
        return email


class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ("category", "skill_name", "skill_level")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_form_control_styling(self)
        self.fields["skill_name"].widget.attrs.setdefault("placeholder", "e.g., Java, Drawing, Excel")


class SwapRequestCreateForm(forms.ModelForm):
    class Meta:
        model = SwapRequest
        fields = ("skill_offered", "skill_requested")

    def __init__(self, *args, offered_choices=None, requested_choices=None, **kwargs):
        super().__init__(*args, **kwargs)
        if offered_choices is not None:
            self.fields["skill_offered"] = forms.ChoiceField(choices=offered_choices, label="Skill you offer")
        if requested_choices is not None:
            self.fields["skill_requested"] = forms.ChoiceField(choices=requested_choices, label="Skill you want")
        _apply_form_control_styling(self)

