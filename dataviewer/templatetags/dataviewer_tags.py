from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def url_with(context, **changes):
    """Current query string with some params replaced. None removes a param."""
    params = context["request"].GET.copy()
    for key, value in changes.items():
        if value is None:
            params.pop(key, None)
        else:
            params[key] = value
    encoded = params.urlencode()
    return f"?{encoded}" if encoded else "?"


@register.filter
def sort_toggle(current, column):
    """Next sort value for a column header: asc -> desc -> asc."""
    return f"-{column}" if current == column else column
