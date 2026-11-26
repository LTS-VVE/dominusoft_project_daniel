from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from pages.utils import querystring_without_page, staff_required

from .forms import ResourceForm, ResourceStaffForm
from .models import Category, Resource


def resource_list(request):
    qs = Resource.objects.select_related("category")
    if not request.user.is_staff:
        qs = qs.filter(is_published=True)
    kategori = request.GET.get("kategori", "")
    lloji = request.GET.get("lloji", "")
    gjuha = request.GET.get("gjuha", "")
    q = request.GET.get("q", "").strip()

    if kategori:
        qs = qs.filter(category__slug=kategori)
    if lloji in Resource.Kind.values:
        qs = qs.filter(kind=lloji)
    else:
        lloji = ""
    if gjuha in Resource.Language.values:
        qs = qs.filter(language=gjuha)
    else:
        gjuha = ""
    for term in q.split():
        qs = qs.filter(Q(title__icontains=term) | Q(description__icontains=term))

    page = Paginator(qs, 24).get_page(request.GET.get("page"))
    return render(request, "resources/list.html", {
        "page": page,
        "extra": querystring_without_page(request),
        "categories": Category.objects.filter(resources__is_published=True).distinct(),
        "kinds": Resource.Kind.choices,
        "languages": Resource.Language.choices,
        "f": {"kategori": kategori, "lloji": lloji, "gjuha": gjuha, "q": q},
    })


@login_required
def resource_suggest(request):
    if request.method == "POST":
        form = ResourceForm(request.POST)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.added_by = request.user
            resource.is_published = False
            resource.save()
            messages.success(request, "Faleminderit! Burimi do të shqyrtohet nga ekipi përpara se të publikohet.")
            return redirect("resources:list")
    else:
        form = ResourceForm()
    return render(request, "resources/suggest.html", {"form": form})


@staff_required
def resource_create(request):
    if request.method == "POST":
        form = ResourceStaffForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.added_by = request.user
            obj.save()
            messages.success(request, "Burimi u shtua.")
            return redirect("resources:list")
    else:
        form = ResourceStaffForm(initial={"is_published": True})
    return render(request, "resources/form.html", {"form": form})


@staff_required
def resource_edit(request, pk):
    obj = get_object_or_404(Resource, pk=pk)
    if request.method == "POST":
        form = ResourceStaffForm(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Ndryshimet u ruajtën.")
            return redirect("resources:list")
    else:
        form = ResourceStaffForm(instance=obj)
    return render(request, "resources/form.html", {"form": form, "resource": obj})
