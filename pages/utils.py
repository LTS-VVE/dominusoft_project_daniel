from functools import wraps
from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.utils.text import slugify


def querystring_without_page(request):
    """Current GET parameters without 'page', for pagination links."""
    params = [(k, v) for k, vs in request.GET.lists() for v in vs if k != "page"]
    return urlencode(params)


def staff_required(view):
    """Anonymous users go to the login page, logged-in non-staff get a 403."""
    @login_required
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapper


def unique_slug(model, text, instance=None, max_length=50):
    """Make a URL slug from text that is not used yet by another row of model."""
    base = slugify(text)[:max_length].strip("-") or "item"
    slug, n = base, 2
    qs = model.objects.all()
    if instance is not None and instance.pk:
        qs = qs.exclude(pk=instance.pk)
    while qs.filter(slug=slug).exists():
        slug = f"{base}-{n}"
        n += 1
    return slug
