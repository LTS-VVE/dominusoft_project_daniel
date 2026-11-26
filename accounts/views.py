from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from pages.utils import querystring_without_page

from .forms import ProfileForm, SignupForm
from .models import Profile


def signup(request):
    if request.user.is_authenticated:
        return redirect("tickets:ticket_list")
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome aboard.")
            return redirect("tickets:ticket_list")
    else:
        form = SignupForm()
    return render(request, "accounts/signup.html", {"form": form})


@login_required
def profile_edit(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profili u ruajt.")
            return redirect("profile_edit")
    else:
        form = ProfileForm(instance=profile)
    return render(request, "accounts/profile_form.html", {"form": form, "profile": profile})


def member_list(request):
    qs = Profile.objects.filter(is_public=True).select_related("user").order_by("display_name", "user__username")
    page = Paginator(qs, 24).get_page(request.GET.get("page"))
    return render(request, "accounts/member_list.html", {"page": page, "extra": querystring_without_page(request)})


def member_detail(request, username):
    user = get_object_or_404(get_user_model(), username=username)
    profile, _ = Profile.objects.get_or_create(user=user)
    is_owner = request.user.is_authenticated and request.user == user
    if not (profile.is_public or is_owner or request.user.is_staff):
        raise Http404
    articles = user.articles.filter(status="published").select_related("category")[:10]
    return render(request, "accounts/member_detail.html", {
        "member": user, "profile": profile, "is_owner": is_owner, "can_edit": is_owner or request.user.is_staff, "articles": articles,
    })


@login_required
def member_edit(request, username):
    """Owner or staff can edit a profile (including its photo)."""
    target = get_object_or_404(get_user_model(), username=username)
    if not (request.user == target or request.user.is_staff):
        raise PermissionDenied
    profile, _ = Profile.objects.get_or_create(user=target)
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profili u ruajt.")
            return redirect("members:detail", username=target.username)
    else:
        form = ProfileForm(instance=profile)
    return render(request, "accounts/profile_form.html", {"form": form, "profile": profile, "member": target})
