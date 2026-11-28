import json

from django import forms

from .query import DISPLAYS, ConfigError, clean_config
from .registry import get_source, sources_for


class BlockCreateForm(forms.Form):
    name = forms.CharField(max_length=100)
    source = forms.ChoiceField()

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["source"].choices = [(s.key, f"{s.label} ({s.key})") for s in sources_for(user)]


class BlockConfigForm(forms.Form):
    name = forms.CharField(max_length=100)
    columns = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple)
    ordering = forms.ChoiceField(required=False)
    descending = forms.BooleanField(required=False)
    display = forms.ChoiceField(choices=[(d, d.title()) for d in sorted(DISPLAYS)])
    group_by = forms.ChoiceField(required=False, help_text="Needed for Board and Chart.")
    pagination = forms.IntegerField(min_value=1, max_value=100, initial=25)
    filters = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 4, "class": "font-monospace"}),
        help_text='JSON, e.g. {"status": "open", "created_at__gte": "2026-01-01"}',
    )

    def __init__(self, *args, source, **kwargs):
        super().__init__(*args, **kwargs)
        self.source = source
        choices = [(f, f) for f in source.fields]
        self.fields["columns"].choices = choices
        self.fields["ordering"].choices = [("", "(default)")] + choices
        self.fields["group_by"].choices = [("", "(none)")] + choices
        for name, field in self.fields.items():
            if name not in {"columns", "descending"}:
                field.widget.attrs.setdefault("class", "form-control")

    @classmethod
    def initial_from_config(cls, name, config):
        ordering = config.get("ordering", "")
        return {
            "name": name,
            "columns": config.get("fields", []),
            "ordering": ordering.lstrip("-"),
            "descending": ordering.startswith("-"),
            "display": config.get("display", "table"),
            "group_by": config.get("group_by", ""),
            "pagination": config.get("pagination", 25),
            "filters": json.dumps(config.get("filters", {}), indent=2) if config.get("filters") else "",
        }

    def clean_filters(self):
        raw = self.cleaned_data["filters"].strip()
        if not raw:
            return {}
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise forms.ValidationError(f"Not valid JSON: {exc}")
        if not isinstance(value, dict):
            raise forms.ValidationError("Filters must be a JSON object.")
        return value

    def clean(self):
        data = super().clean()
        if self.errors:
            return data
        ordering = data.get("ordering") or ""
        if ordering and data.get("descending"):
            ordering = "-" + ordering
        config = {
            "source": self.source.key,
            "fields": data["columns"],
            "filters": data["filters"],
            "ordering": ordering,
            "display": data["display"],
            "group_by": data.get("group_by") or "",
            "pagination": data["pagination"],
        }
        try:
            self.config = clean_config(config, self.source)
        except ConfigError as exc:
            raise forms.ValidationError(str(exc))
        return data


class SavedViewForm(forms.Form):
    name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={"class": "form-control"}))


class ImportConfigForm(forms.Form):
    file = forms.FileField(help_text="A .json file exported from the Data Viewer.")

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_file(self):
        upload = self.cleaned_data["file"]
        if upload.size > 100_000:
            raise forms.ValidationError("File too large.")
        try:
            payload = json.load(upload)
            block = payload["block"]
            source = get_source(block["config"]["source"])
        except Exception:
            raise forms.ValidationError("This is not a valid Data Viewer export.")
        if not self.user.has_perm(source.view_perm):
            raise forms.ValidationError("You don't have access to that data source.")
        try:
            self.config = clean_config(block["config"], source)
        except ConfigError as exc:
            raise forms.ValidationError(str(exc))
        self.block_name = str(block.get("name") or "Imported block")[:100]
        return upload
