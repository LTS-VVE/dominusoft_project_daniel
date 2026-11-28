"""Schema snapshots and comparisons."""
from .introspect import describe_all  # noqa: F401  (re-exported for tests)
from .models import SchemaSnapshot


def take_snapshot(user=None, label=""):
    return SchemaSnapshot.objects.create(data=describe_all(), created_by=user, label=label)


def _fields(model_info):
    return {f["name"]: f for f in model_info["fields"]}


def compare(old, new):
    """Returns what changed between two describe_all() dicts."""
    old_keys, new_keys = set(old), set(new)
    changed = {}
    for key in sorted(old_keys & new_keys):
        before, after = _fields(old[key]), _fields(new[key])
        added = sorted(set(after) - set(before))
        removed = sorted(set(before) - set(after))
        modified = []
        for name in sorted(set(before) & set(after)):
            if before[name] != after[name]:
                diffs = {k: (before[name].get(k), after[name].get(k))
                         for k in set(before[name]) | set(after[name])
                         if before[name].get(k) != after[name].get(k)}
                modified.append({"field": name, "changes": diffs})
        if added or removed or modified:
            changed[key] = {"added": added, "removed": removed, "modified": modified}
    return {
        "models_added": sorted(new_keys - old_keys),
        "models_removed": sorted(old_keys - new_keys),
        "models_changed": changed,
    }
