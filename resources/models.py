from django.conf import settings
from django.core.validators import URLValidator
from django.db import models

from pages.images import IMAGE_VALIDATORS, ImageModelMixin, upload_to


class Category(models.Model):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=70, unique=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Resource(ImageModelMixin):
    class Kind(models.TextChoices):
        ARTICLE = "article", "Artikull"
        VIDEO = "video", "Video"
        COURSE = "course", "Kurs"
        TOOL = "tool", "Mjet"
        BOOK = "book", "Libër"
        OTHER = "other", "Tjetër"

    class Language(models.TextChoices):
        SQ = "sq", "Shqip"
        EN = "en", "English"
        OTHER = "other", "Tjetër"

    title = models.CharField(max_length=150)
    image = models.ImageField(upload_to=upload_to, blank=True, validators=IMAGE_VALIDATORS)
    image_max_px = 800
    url = models.URLField(max_length=500, validators=[URLValidator(schemes=["http", "https"])])
    description = models.CharField(max_length=400)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="resources")
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.ARTICLE)
    language = models.CharField(max_length=5, choices=Language.choices, default=Language.EN)
    is_free = models.BooleanField(default=True)
    is_published = models.BooleanField(default=False, help_text="Suggestions from members stay hidden until you publish them.")
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="resources_added"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
