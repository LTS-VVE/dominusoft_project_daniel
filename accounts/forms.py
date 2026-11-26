from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Profile, User


class SignupForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["avatar", "display_name", "headline", "bio", "location", "skills", "website", "is_public"]
        labels = {
            "avatar": "Fotoja e profilit",
            "display_name": "Emri që shfaqet",
            "headline": "Titulli",
            "bio": "Rreth teje",
            "location": "Vendndodhja",
            "skills": "Aftësitë (ndaji me presje)",
            "website": "Faqja personale",
            "is_public": "Shfaqe profilin tim publikisht në listën e anëtarëve",
        }
        widgets = {
            "avatar": forms.ClearableFileInput(attrs={"accept": "image/jpeg,image/png,image/webp"}),
            "display_name": forms.TextInput(attrs={"class": "form-control"}),
            "headline": forms.TextInput(attrs={"class": "form-control"}),
            "bio": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "location": forms.TextInput(attrs={"class": "form-control"}),
            "skills": forms.TextInput(attrs={"class": "form-control", "placeholder": "Python, Office Tools, Graphic Design..."}),
            "website": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://example.com"}),
        }
