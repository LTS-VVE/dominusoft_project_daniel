from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import URLValidator
from django.db import models

from pages.images import IMAGE_VALIDATORS, ImageModelMixin, upload_to


class User(AbstractUser):
    pass


class Profile(ImageModelMixin):
    image_field = "avatar"
    image_max_px = 512
    image_square = True

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    avatar = models.ImageField(upload_to=upload_to, blank=True, validators=IMAGE_VALIDATORS)
    display_name = models.CharField(max_length=60, blank=True)
    headline = models.CharField(max_length=100, blank=True, help_text="For example: Linux admin, student, designer")
    bio = models.TextField(max_length=1000, blank=True)
    location = models.CharField(max_length=60, blank=True)
    skills = models.CharField(max_length=200, blank=True, help_text="Separate with commas")
    website = models.URLField(blank=True, validators=[URLValidator(schemes=["http", "https"])])
    # Opt-in, opt out, meow
    is_public = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user}"

    @property
    def name(self):
        return self.display_name or self.user.username

    @property
    def skill_list(self):
        return [s.strip() for s in self.skills.split(",") if s.strip()][:12]
