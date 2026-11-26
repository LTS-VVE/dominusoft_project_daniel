from django.db.models import Count, Q
from django.shortcuts import render
from django.utils import timezone

from events.models import Event
from knowledge.models import Article
from tickets.models import Ticket

from .search import search_all


def home(request):
    stats = None
    if request.user.is_authenticated:
        qs = Ticket.objects.all()
        if not request.user.is_staff:
            qs = qs.filter(requester=request.user)
        stats = qs.aggregate(
            total=Count("id"),
            open=Count("id", filter=Q(status=Ticket.Status.OPEN)),
            progress=Count("id", filter=Q(status=Ticket.Status.IN_PROGRESS)),
            closed=Count("id", filter=Q(status=Ticket.Status.CLOSED)),
        )
    now = timezone.now()
    articles = Article.objects.filter(status=Article.Status.PUBLISHED).select_related("category")[:3]
    events = (
        Event.objects.filter(is_published=True)
        .exclude(Q(ends_at__lt=now) | Q(ends_at__isnull=True, starts_at__lt=now))
        .order_by("starts_at")[:3]
    )
    return render(request, "pages/index.html", {"stats": stats, "articles": articles, "events": events})


def about(request):
    return render(request, "pages/about.html")


def contact(request):
    return render(request, "pages/contact.html")


def status(request):
    return render(request, "pages/status.html")


def search(request):
    query = request.GET.get("q", "").strip()
    results = search_all(query, request.user)
    total = sum(len(v) for v in results.values())
    return render(request, "pages/search.html", {"query": query, "total": total, **results})
