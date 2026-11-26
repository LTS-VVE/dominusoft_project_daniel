from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from .forms import TicketForm, StaffTicketForm, CommentForm
from .models import Ticket


def _check_access(request, ticket):
    if ticket.requester != request.user and not request.user.is_staff:
        raise PermissionDenied


@login_required
def ticket_list(request):
    qs = Ticket.objects.select_related("category", "requester")
    if not request.user.is_staff:
        qs = qs.filter(requester=request.user)
    return render(request, "tickets/list.html", {"tickets": qs})


@login_required
def ticket_create(request):
    if request.method == "POST":
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.requester = request.user
            ticket.save()
            messages.success(request, "Ticket created successfully.")
            return redirect("tickets:ticket_detail", pk=ticket.pk)
    else:
        form = TicketForm()
    return render(request, "tickets/form.html", {"form": form})


@login_required
def ticket_detail(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    _check_access(request, ticket)
    return render(request, "tickets/detail.html", {
        "ticket": ticket,
        "comment_form": CommentForm(),
    })


@login_required
def ticket_update(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    _check_access(request, ticket)
    FormClass = StaffTicketForm if request.user.is_staff else TicketForm
    if request.method == "POST":
        form = FormClass(request.POST, instance=ticket)
        if form.is_valid():
            form.save()
            messages.success(request, "Ticket updated successfully.")
            return redirect("tickets:ticket_detail", pk=ticket.pk)
    else:
        form = FormClass(instance=ticket)
    return render(request, "tickets/form.html", {"form": form, "ticket": ticket})


@login_required
def comment_create(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    _check_access(request, ticket)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.ticket = ticket
            comment.author = request.user
            comment.save()
            messages.success(request, "Comment added.")
    return redirect("tickets:ticket_detail", pk=ticket.pk)