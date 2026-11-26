from django import forms
from django.utils.text import slugify

from pages.utils import unique_slug

from .models import Article, Category

IMAGE_WIDGET = forms.ClearableFileInput(attrs={"accept": "image/jpeg,image/png,image/webp"})


class ArticleForm(forms.ModelForm):
    new_category = forms.CharField(
        label="Ose krijo kategori të re", max_length=60, required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = Article
        fields = ["title", "slug", "summary", "category", "new_category", "image", "body", "status"]
        labels = {
            "title": "Titulli", "slug": "Slug (adresa; lëre bosh që të krijohet vetë)",
            "summary": "Përmbledhje", "category": "Kategoria", "image": "Imazhi kryesor",
            "body": "Teksti (Markdown)", "status": "Statusi",
        }
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "slug": forms.TextInput(attrs={"class": "form-control"}),
            "summary": forms.TextInput(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "image": IMAGE_WIDGET,
            "body": forms.Textarea(attrs={"class": "form-control", "rows": 14}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slug"].required = False
        self.fields["category"].required = False
        self.fields["category"].empty_label = "Zgjidh kategorinë"

    def clean(self):
        data = super().clean()
        if not data.get("category") and not (data.get("new_category") or "").strip():
            self.add_error("category", "Zgjidh një kategori ose krijo një të re.")
        slug = (data.get("slug") or "").strip()
        if not slug and data.get("title"):
            data["slug"] = unique_slug(Article, data["title"], self.instance, max_length=60)
        return data

    def save(self, commit=True):
        article = super().save(commit=False)
        name = (self.cleaned_data.get("new_category") or "").strip()
        if name and not self.cleaned_data.get("category"):
            article.category, _ = Category.objects.get_or_create(
                name=name, defaults={"slug": unique_slug(Category, name, max_length=60)}
            )
        if commit:
            article.save()
        return article
