"""Turn a block config (untrusted JSON) into a safe Django queryset.

Every name that comes from the browser is checked against the registry
before it gets anywhere near the ORM. No raw SQL, no relation traversal.
"""
import datetime

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.utils import timezone

from .registry import get_source

ALLOWED_LOOKUPS = {"exact", "iexact", "icontains", "gt", "gte", "lt", "lte", "in", "isnull", "date"}
DISPLAYS = {"table", "cards", "board", "chart"}
MAX_PAGE_SIZE = 100
BOARD_LIMIT = 200


class ConfigError(ValueError):
    pass


def clean_config(config, source):
    """Validate a config dict against a source. Returns a new, clean dict."""
    if not isinstance(config, dict):
        raise ConfigError("Config must be a JSON object.")

    fields = config.get("fields") or list(source.fields)
    if not isinstance(fields, list):
        raise ConfigError("'fields' must be a list.")
    unknown = [f for f in fields if f not in source.fields]
    if unknown:
        raise ConfigError(f"Unknown or hidden fields: {', '.join(map(str, unknown))}")

    filters = {}
    raw_filters = config.get("filters") or {}
    if not isinstance(raw_filters, dict):
        raise ConfigError("'filters' must be an object.")
    for key, value in raw_filters.items():
        # "status" or "created_at__gte". Anything deeper ("category__name") is rejected,
        # because "name" is not an allowed lookup. That blocks relation traversal.
        name, _, lookup = str(key).partition("__")
        lookup = lookup or "exact"
        if name not in source.fields:
            raise ConfigError(f"Cannot filter on '{name}'.")
        if lookup not in ALLOWED_LOOKUPS:
            raise ConfigError(f"Lookup '{lookup}' is not allowed.")
        if lookup == "in" and not isinstance(value, list):
            raise ConfigError(f"'{key}' needs a list.")
        filters[f"{name}__{lookup}"] = value

    ordering = config.get("ordering") or ""
    if ordering and ordering.lstrip("-") not in source.fields:
        raise ConfigError(f"Cannot order by '{ordering}'.")

    try:
        page_size = int(config.get("pagination", 25))
    except (TypeError, ValueError):
        raise ConfigError("'pagination' must be a number.") from None
    page_size = max(1, min(page_size, MAX_PAGE_SIZE))

    display = config.get("display", "table")
    if display not in DISPLAYS:
        raise ConfigError(f"Unknown display '{display}'.")

    group_by = config.get("group_by") or ""
    if display in {"board", "chart"}:
        if group_by not in source.fields:
            raise ConfigError(f"Display '{display}' needs a valid 'group_by' field.")

    widths = {}
    for name, px in (config.get("column_widths") or {}).items():
        if name in fields:
            try:
                widths[name] = max(60, min(int(px), 600))
            except (TypeError, ValueError):
                raise ConfigError(f"Width for '{name}' must be a number.") from None

    return {
        "source": source.key,
        "fields": fields,
        "filters": filters,
        "ordering": ordering,
        "pagination": page_size,
        "display": display,
        "group_by": group_by,
        "column_widths": widths,
    }


def build_queryset(user, config, search="", sort=""):
    """Returns (source, clean_config, queryset). Raises PermissionDenied or ConfigError."""
    source = get_source(config.get("source", ""))
    if not user.has_perm(source.view_perm):
        raise PermissionDenied
    cfg = clean_config(config, source)

    qs = source.model._default_manager.all()

    related = [n for n in cfg["fields"] if source.field(n).many_to_one or source.field(n).one_to_one]
    if related:
        qs = qs.select_related(*related)

    try:
        qs = qs.filter(**cfg["filters"])
    except (ValueError, TypeError, ValidationError) as exc:
        raise ConfigError(f"Bad filter value: {exc}") from None

    if search and source.search_fields:
        q = Q()
        for name in source.search_fields:
            q |= Q(**{f"{name}__icontains": search})
        qs = qs.filter(q)

    # A sort from the URL wins over the saved ordering, but only if it is valid.
    if sort and sort.lstrip("-") in cfg["fields"]:
        ordering = sort
    else:
        ordering = cfg["ordering"] or "-pk"
    # Add pk as a tiebreaker so pagination is stable.
    tiebreak = [] if ordering.lstrip("-") in ("pk", "id") else ["-pk"]
    return source, cfg, qs.order_by(ordering, *tiebreak)


def display_value(obj, name):
    field = obj._meta.get_field(name)
    if field.choices:
        return getattr(obj, f"get_{name}_display")()
    value = getattr(obj, name)
    if isinstance(value, datetime.datetime):
        if timezone.is_aware(value):
            value = timezone.localtime(value)
        return value.strftime("%Y-%m-%d %H:%M")
    return "" if value is None else value


def link_target(obj, name):
    """(source_key, pk) if this field points at another registered model, else None."""
    from .introspect import is_registered

    field = obj._meta.get_field(name)
    if not (field.many_to_one or field.one_to_one):
        return None
    target = field.related_model._meta.label
    pk = getattr(obj, field.attname)
    if pk is None or not is_registered(target):
        return None
    return target, pk


def build_rows(objects, fields):
    rows = []
    for obj in objects:
        cells = [{"value": display_value(obj, f), "link": link_target(obj, f)} for f in fields]
        rows.append({"pk": obj.pk, "cells": cells, "obj": obj})
    return rows


def paginate(qs, page_size, page_number):
    return Paginator(qs, page_size).get_page(page_number)


def board_columns(source, cfg, qs):
    """Group up to BOARD_LIMIT records into columns by cfg['group_by']."""
    name = cfg["group_by"]
    field = source.field(name)
    columns = {}
    if field.choices:
        for value, label in field.choices:
            columns[str(label)] = []
    for row in build_rows(qs[:BOARD_LIMIT], cfg["fields"]):
        key = str(display_value(row["obj"], name) or "(empty)")
        columns.setdefault(key, []).append(row)
    return columns


def chart_data(source, cfg, qs):
    """Record counts per value of cfg['group_by'], ready for Chart.js."""
    name = cfg["group_by"]
    field = source.field(name)
    counts = qs.order_by().values(name).annotate(n=Count("pk")).order_by(name)
    raw = [(c[name], c["n"]) for c in counts]

    if field.choices:
        lookup = {str(v): str(label) for v, label in field.choices}
        labels = [lookup.get(str(v), str(v)) for v, _ in raw]
    elif field.many_to_one or field.one_to_one:
        objs = field.related_model._default_manager.in_bulk([v for v, _ in raw if v is not None])
        labels = [str(objs.get(v, "(empty)")) for v, _ in raw]
    else:
        labels = ["(empty)" if v is None else str(v) for v, _ in raw]
    return {"labels": labels, "data": [n for _, n in raw]}
