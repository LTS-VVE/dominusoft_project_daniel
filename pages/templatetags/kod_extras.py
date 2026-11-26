
import markdown
import nh3

from django import template
from django.templatetags.static import static
from django.utils.html import format_html
from django.utils.safestring import mark_safe


register = template.Library()


MONTHS = [
    "Janar",
    "Shkurt",
    "Mars",
    "Prill",
    "Maj",
    "Qershor",
    "Korrik",
    "Gusht",
    "Shtator",
    "Tetor",
    "Nëntor",
    "Dhjetor",
]

WEEKDAYS = [
    "E hënë",
    "E martë",
    "E mërkurë",
    "E enjte",
    "E premte",
    "E shtunë",
    "E diel",
]


@register.filter(expects_localtime=True)
def sq_date(value):
    """Format a date using Albanian month names."""
    if not value:
        return ""

    month = MONTHS[value.month - 1]
    return f"{value.day} {month} {value.year}"


@register.filter(expects_localtime=True)
def sq_month_short(value):
    """Return the abbreviated Albanian month name."""
    if not value:
        return ""

    return MONTHS[value.month - 1][:3].upper()


@register.filter(expects_localtime=True)
def sq_weekday(value):
    """Return the Albanian weekday name."""
    if not value:
        return ""

    return WEEKDAYS[value.weekday()]


@register.filter
def markdown_safe(text):
    """Convert Markdown into sanitized HTML."""
    html = markdown.markdown(
        text or "",
        extensions=[
            "fenced_code",
            "tables",
        ],
    )

    return mark_safe(nh3.clean(html))


@register.simple_tag
def hero_style(image=None, default=None):
    """Set the page hero background image."""
    if image:
        url = image.url
    elif default:
        url = static(f"assets/{default}")
    else:
        return ""

    return format_html("--hero-img: url('{}')", url)


@register.inclusion_tag("pages/_avatar.html")
def avatar(user, size=40):
    """Render a user's avatar or their initial as a fallback."""
    profile = getattr(user, "profile", None)
    image = getattr(profile, "avatar", None) if profile else None
    username = getattr(user, "username", "?") or "?"

    return {
        "url": image.url if image else "",
        "initial": username[0].upper(),
        "size": size,
        "font": max(11, int(size * 0.42)),
    }
