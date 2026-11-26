from django import forms

from pages.utils import unique_slug

from .models import Category, Resource

LABELS = {
    "title": "Titulli", "url": "Lidhja (URL)", "description": "Përshkrimi", "category": "Kategoria",
    "kind": "Lloji", "language": "Gjuha", "is_free": "Falas", "image": "Imazhi", "is_published": "Publikuar",
}
WIDGETS = {
    "title": forms.TextInput(attrs={"class": "form-control"}),
    "url": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://"}),
    "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
    "category": forms.Select(attrs={"class": "form-select"}),
    "kind": forms.Select(attrs={"class": "form-select"}),
    "language": forms.Select(attrs={"class": "form-select"}),
    "image": forms.ClearableFileInput(attrs={"accept": "image/jpeg,image/png,image/webp"}),
}


class ResourceForm(forms.ModelForm):
    """Member suggestion (no image, never published directly)."""
    class Meta:
        model = Resource
        fields = ["title", "url", "description", "category", "kind", "language", "is_free"]
        labels = LABELS
        widgets = WIDGETS


class ResourceStaffForm(forms.ModelForm):
    new_category = forms.CharField(label="Ose krijo kategori të re", max_length=60, required=False,
                                   widget=forms.TextInput(attrs={"class": "form-control"}))

    class Meta:
        model = Resource
        fields = ["title", "image", "url", "description", "category", "new_category", "kind", "language",
                  "is_free", "is_published"]
        labels = LABELS
        widgets = WIDGETS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].required = False

    def clean(self):
        data = super().clean()
        if not data.get("category") and not (data.get("new_category") or "").strip():
            self.add_error("category", "Zgjidh një kategori ose krijo një të re.")
        return data

    def save(self, commit=True):
        obj = super().save(commit=False)
        name = (self.cleaned_data.get("new_category") or "").strip()
        if name and not self.cleaned_data.get("category"):
            obj.category, _ = Category.objects.get_or_create(
                name=name, defaults={"slug": unique_slug(Category, name, max_length=60)})
        if commit:
            obj.save()
        return obj
