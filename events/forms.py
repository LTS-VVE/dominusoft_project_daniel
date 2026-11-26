from django import forms

from pages.utils import unique_slug

from .models import Event

DT_FORMAT = "%Y-%m-%dT%H:%M"


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ["title", "slug", "image", "description", "location", "online_url",
                  "starts_at", "ends_at", "capacity", "is_published"]
        labels = {
            "title": "Titulli", "slug": "Slug (adresa; lëre bosh që të krijohet vetë)",
            "image": "Imazhi", "description": "Përshkrimi (Markdown)", "location": "Vendi",
            "online_url": "Lidhja online (shfaqet vetëm për të regjistruarit)",
            "starts_at": "Fillon", "ends_at": "Mbaron (opsionale)",
            "capacity": "Kapaciteti (bosh = pa kufi)", "is_published": "Publikuar",
        }
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "slug": forms.TextInput(attrs={"class": "form-control"}),
            "image": forms.ClearableFileInput(attrs={"accept": "image/jpeg,image/png,image/webp"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 8}),
            "location": forms.TextInput(attrs={"class": "form-control"}),
            "online_url": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://"}),
            "starts_at": forms.DateTimeInput(format=DT_FORMAT, attrs={"type": "datetime-local", "class": "form-control"}),
            "ends_at": forms.DateTimeInput(format=DT_FORMAT, attrs={"type": "datetime-local", "class": "form-control"}),
            "capacity": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slug"].required = False
        for name in ("starts_at", "ends_at"):
            self.fields[name].input_formats = [DT_FORMAT, "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S"]

    def clean(self):
        data = super().clean()
        start, end = data.get("starts_at"), data.get("ends_at")
        if start and end and end <= start:
            self.add_error("ends_at", "Ora e mbarimit duhet të jetë pas fillimit.")
        if not (data.get("slug") or "").strip() and data.get("title"):
            data["slug"] = unique_slug(Event, data["title"], self.instance, max_length=60)
        return data
