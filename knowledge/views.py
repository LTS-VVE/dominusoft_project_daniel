from django.contrib import messages
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from pages.utils import querystring_without_page, staff_required

from .forms import ArticleForm
from .models import Article, Category


def article_list(request):
    qs = Article.objects.select_related("category", "author")
    if not request.user.is_staff:
        qs = qs.filter(status=Article.Status.PUBLISHED)
    active = request.GET.get("kategori", "")
    if active:
        qs = qs.filter(category__slug=active)
    page = Paginator(qs, 12).get_page(request.GET.get("page"))
    categories = Category.objects.filter(articles__status=Article.Status.PUBLISHED).distinct()
    return render(request, "knowledge/list.html", {
        "page": page, "categories": categories, "active": active,
        "extra": querystring_without_page(request),
    })


def article_detail(request, slug):
    article = get_object_or_404(Article.objects.select_related("category", "author"), slug=slug)
    if article.status != Article.Status.PUBLISHED and not request.user.is_staff:
        raise Http404
    related = (
        Article.objects.filter(status=Article.Status.PUBLISHED, category=article.category)
        .exclude(pk=article.pk)[:3]
    )
    return render(request, "knowledge/detail.html", {"article": article, "related": related})


@staff_required
def article_create(request):
    if request.method == "POST":
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.save()
            messages.success(request, "Artikulli u krijua.")
            return redirect(article)
    else:
        form = ArticleForm()
    return render(request, "knowledge/form.html", {"form": form})


@staff_required
def article_edit(request, slug):
    article = get_object_or_404(Article, slug=slug)
    if request.method == "POST":
        form = ArticleForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            article = form.save()
            messages.success(request, "Ndryshimet u ruajtën.")
            return redirect(article)
    else:
        form = ArticleForm(instance=article)
    return render(request, "knowledge/form.html", {"form": form, "article": article})
