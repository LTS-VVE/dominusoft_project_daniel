from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

from pages.images import IMAGE_VALIDATORS, ImageModelMixin, upload_to


class Event(ImageModelMixin):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField(help_text="Markdown is supported.")
    image = models.ImageField(upload_to=upload_to, blank=True, validators=IMAGE_VALIDATORS)
    location = models.CharField(max_length=150, blank=True, help_text="Address or place name. Leave empty for online events.")
    online_url = models.URLField(blank=True, help_text="Only shown to people who sign up.")
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(null=True, blank=True)
    capacity = models.PositiveIntegerField(null=True, blank=True, help_text="Leave empty for unlimited.")
    is_published = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="events_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["starts_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("events:detail", args=[self.slug])

    @property
    def is_past(self):
        return (self.ends_at or self.starts_at) < timezone.now()

    @property
    def spots_left(self):
        if self.capacity is None:
            return None
        return max(0, self.capacity - self.rsvps.count())

    @property
    def is_full(self):
        return self.capacity is not None and self.rsvps.count() >= self.capacity


class RSVP(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="rsvps")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="rsvps")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["event", "user"], name="one_rsvp_per_user")]

    def __str__(self):
        return f"{self.user} -> {self.event}"
