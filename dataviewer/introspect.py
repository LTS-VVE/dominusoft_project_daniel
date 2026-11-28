from .registry import all_sources, get_source, UnknownSource


def relation_kind(field):
    if field.many_to_many:
        return "many_to_many"
    if field.one_to_one:
        return "one_to_one"
    if field.many_to_one:
        return "foreign_key"
    return "reverse"


def describe_field(field):
    info = {
        "name": field.name,
        "type": field.get_internal_type(),
        "null": field.null,
        "blank": getattr(field, "blank", False),
        "unique": field.unique,
        "primary_key": field.primary_key,
    }
    if getattr(field, "max_length", None):
        info["max_length"] = field.max_length
    if field.choices:
        info["choices"] = [[str(v), str(label)] for v, label in field.choices]
    if field.is_relation and field.related_model:
        target = field.related_model._meta.label
        info["relation"] = {"kind": relation_kind(field), "to": target, "browsable": is_registered(target)}
    return info


def is_registered(key):
    try:
        get_source(key)
        return True
    except UnknownSource:
        return False


def describe_source(source):
    meta = source.model._meta
    return {
        "source": source.key,
        "label": source.label,
        "db_table": meta.db_table,
        "fields": [describe_field(source.field(name)) for name in source.fields],
        "search_fields": list(source.search_fields),
        "reverse_relations": [
            {
                "accessor": rel.get_accessor_name(),
                "from": rel.related_model._meta.label,
                "via": rel.field.name,
                "browsable": is_registered(rel.related_model._meta.label),
            }
            for rel in meta.related_objects
        ],
        "indexes": [{"name": i.name, "fields": list(i.fields)} for i in meta.indexes],
        "constraints": [{"name": c.name, "type": type(c).__name__} for c in meta.constraints],
        "unique_together": [list(u) for u in meta.unique_together],
    }


def describe_all():
    return {s.key: describe_source(s) for s in all_sources()}
