from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, F, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from pages.utils import staff_required

from .forms import EventForm
from .models import Event, RSVP


def _visible(request):
    qs = Event.objects.all()
    if not request.user.is_staff:
        qs = qs.filter(is_published=True)
    return qs


def event_list(request):
    now = timezone.now()
    show_past = request.GET.get("te") == "kaluara"
    qs = _visible(request).annotate(going=Count("rsvps"))
    ended = Q(ends_at__lt=now) | Q(ends_at__isnull=True, starts_at__lt=now)
    if show_past:
        events = qs.filter(ended).order_by("-starts_at")[:30]
    else:
        events = qs.exclude(ended).order_by("starts_at")
    return render(request, "events/list.html", {"events": events, "show_past": show_past})


def event_detail(request, slug):
    event = get_object_or_404(_visible(request), slug=slug)
    going = request.user.is_authenticated and event.rsvps.filter(user=request.user).exists()
    return render(request, "events/detail.html", {
        "event": event,
        "going": going,
        "going_count": event.rsvps.count(),
    })


@login_required
@require_POST
def event_rsvp(request, slug):
    event = get_object_or_404(_visible(request), slug=slug)
    with transaction.atomic():
        # Lock the event row so two people cannot take the last spot at once.
        event = Event.objects.select_for_update().get(pk=event.pk)
        existing = RSVP.objects.filter(event=event, user=request.user)
        if existing.exists():
            existing.delete()
            messages.success(request, "Pjesëmarrja u anulua.")
        elif event.is_past:
            messages.error(request, "Kjo ngjarje ka përfunduar.")
        elif event.is_full:
            messages.error(request, "Ngjarja është plot.")
        else:
            RSVP.objects.create(event=event, user=request.user)
            messages.success(request, "Je regjistruar. Shihemi atje!")
    return redirect(event)


@staff_required
def event_create(request):
    if request.method == "POST":
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()
            messages.success(request, "Ngjarja u krijua.")
            return redirect(event)
    else:
        form = EventForm()
    return render(request, "events/form.html", {"form": form})


@staff_required
def event_edit(request, slug):
    event = get_object_or_404(Event, slug=slug)
    if request.method == "POST":
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            event = form.save()
            messages.success(request, "Ndryshimet u ruajtën.")
            return redirect(event)
    else:
        form = EventForm(instance=event)
    return render(request, "events/form.html", {"form": form, "event": event})
