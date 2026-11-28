"""The allowlist. Only models registered here can ever be seen in the Data Viewer."""
from dataclasses import dataclass

# Field names that are never exposed, even if someone registers them by mistake.
SENSITIVE_FIELDS = {"password", "token", "secret", "api_key", "key"}


class UnknownSource(LookupError):
    pass


@dataclass(frozen=True)
class Source:
    model: type
    fields: tuple
    search_fields: tuple
    label: str

    @property
    def key(self):
        # "tickets.Ticket"
        return self.model._meta.label

    @property
    def view_perm(self):
        meta = self.model._meta
        return f"{meta.app_label}.view_{meta.model_name}"

    def field(self, name):
        return self.model._meta.get_field(name)


_registry = {}


def register(model, fields=None, exclude=(), search_fields=(), label=None):
    meta = model._meta
    if fields is None:
        fields = [f.name for f in meta.concrete_fields]
    blocked = set(exclude) | SENSITIVE_FIELDS
    fields = [name for name in fields if name not in blocked]
    search_fields = [name for name in search_fields if name not in blocked]

    # Fail loudly on typos at startup, not later in a request.
    for name in [*fields, *search_fields]:
        meta.get_field(name)

    source = Source(
        model=model,
        fields=tuple(fields),
        search_fields=tuple(search_fields),
        label=label or str(meta.verbose_name_plural).title(),
    )
    _registry[source.key] = source
    return source


def get_source(key):
    try:
        return _registry[key]
    except KeyError:
        raise UnknownSource(key) from None


def all_sources():
    return sorted(_registry.values(), key=lambda s: s.key)


def sources_for(user):
    return [s for s in all_sources() if user.has_perm(s.view_perm)]
