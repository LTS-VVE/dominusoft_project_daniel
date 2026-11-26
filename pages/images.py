"""Safe image uploads shared by articles, events, resources and profiles.

Every uploaded image is validated (type, size, dimensions), then re-encoded:
resized, rotated according to EXIF and stripped of all metadata (GPS location,
camera info). The original file is never stored.
"""
import io
import os
import uuid

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.validators import FileExtensionValidator
from django.db import models
from PIL import Image, ImageOps

MAX_UPLOAD_MB = 5
MAX_DIMENSION = 8000  # pixels, per side
ALLOWED_EXTENSIONS = ["jpg", "jpeg", "png", "webp"]


def upload_to(instance, filename):
    ext = os.path.splitext(filename)[1].lower() or ".jpg"
    return f"{instance._meta.app_label}/{uuid.uuid4().hex}{ext}"


def validate_image_size(f):
    if f.size > MAX_UPLOAD_MB * 1024 * 1024:
        raise ValidationError(f"Imazhi është shumë i madh (maksimumi {MAX_UPLOAD_MB} MB).")


def validate_image_dimensions(f):
    try:
        img = Image.open(f)
        width, height = img.size
    except Exception:
        raise ValidationError("Ky nuk është një imazh i vlefshëm.")
    finally:
        try:
            f.seek(0)
        except Exception:
            pass
    if width > MAX_DIMENSION or height > MAX_DIMENSION:
        raise ValidationError(f"Imazhi është shumë i madh në pixel (maksimumi {MAX_DIMENSION}px).")


IMAGE_VALIDATORS = [
    FileExtensionValidator(ALLOWED_EXTENSIONS),
    validate_image_size,
    validate_image_dimensions,
]


def optimize(upload, max_px, square=False):
    """Return a ContentFile with a clean, resized copy of the uploaded image."""
    upload.seek(0)
    img = Image.open(upload)
    fmt = (img.format or "JPEG").upper()
    img = ImageOps.exif_transpose(img)
    if square:
        img = ImageOps.fit(img, (max_px, max_px), Image.LANCZOS)
    else:
        img.thumbnail((max_px, max_px), Image.LANCZOS)

    buf = io.BytesIO()
    if fmt == "PNG":
        img.save(buf, "PNG", optimize=True)
        ext = ".png"
    elif fmt == "WEBP":
        img.save(buf, "WEBP", quality=85)
        ext = ".webp"
    else:
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        img.save(buf, "JPEG", quality=85, optimize=True, progressive=True)
        ext = ".jpg"
    return ContentFile(buf.getvalue()), ext


class ImageModelMixin(models.Model):
    """Abstract base: optimizes a newly uploaded image and deletes replaced files."""

    image_field = "image"
    image_max_px = 1600
    image_square = False

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        name = self.image_field
        field = getattr(self, name)
        old = None
        if self.pk:
            old = type(self).objects.filter(pk=self.pk).values_list(name, flat=True).first()
        if field and not field._committed:
            content, ext = optimize(field.file, self.image_max_px, self.image_square)
            field.save(uuid.uuid4().hex + ext, content, save=False)
        super().save(*args, **kwargs)
        new = getattr(self, name).name or ""
        if old and old != new:
            field.storage.delete(old)
