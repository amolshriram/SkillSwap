from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Prefetch, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .forms import LoginForm, ProfileForm, RegisterForm, SkillForm, SwapRequestCreateForm
from .models import Conversation, Message, Skill, SwapRequest, User


def home(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "home.html")


@require_http_methods(["GET", "POST"])
def register(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Welcome! Your account has been created.")
        return redirect("dashboard")
    return render(request, "auth/register.html", {"form": form})


class EmailLoginView(LoginView):
    template_name = "auth/login.html"
    authentication_form = LoginForm


login_view = EmailLoginView.as_view()


@require_http_methods(["POST"])
def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("login")


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    offered = request.user.skills.filter(category=Skill.Category.OFFERED)
    wanted = request.user.skills.filter(category=Skill.Category.WANTED)

    incoming = request.user.received_swap_requests.select_related("sender")
    outgoing = request.user.sent_swap_requests.select_related("receiver")
    return render(
        request,
        "dashboard.html",
        {
            "offered": offered,
            "wanted": wanted,
            "incoming": incoming,
            "outgoing": outgoing,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def profile(request: HttpRequest) -> HttpResponse:
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        user = form.save(commit=False)
        user.username = user.email  # keep login identifier aligned to email
        user.save(update_fields=["full_name", "email", "username"])
        messages.success(request, "Profile updated.")
        return redirect("profile")

    skills = request.user.skills.all()
    return render(request, "profile.html", {"form": form, "skills": skills})


@login_required
@require_http_methods(["GET", "POST"])
def skill_add(request: HttpRequest) -> HttpResponse:
    form = SkillForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        skill: Skill = form.save(commit=False)
        skill.user = request.user
        skill.skill_name = skill.skill_name.strip()
        skill.save()
        messages.success(request, "Skill added.")
        return redirect("profile")
    return render(request, "skills/skill_form.html", {"form": form, "title": "Add Skill"})


@login_required
@require_http_methods(["GET", "POST"])
def skill_edit(request: HttpRequest, skill_id: int) -> HttpResponse:
    skill = get_object_or_404(Skill, pk=skill_id, user=request.user)
    form = SkillForm(request.POST or None, instance=skill)
    if request.method == "POST" and form.is_valid():
        updated: Skill = form.save(commit=False)
        updated.skill_name = updated.skill_name.strip()
        updated.save()
        messages.success(request, "Skill updated.")
        return redirect("profile")
    return render(request, "skills/skill_form.html", {"form": form, "title": "Edit Skill"})


@login_required
@require_http_methods(["POST"])
def skill_delete(request: HttpRequest, skill_id: int) -> HttpResponse:
    skill = get_object_or_404(Skill, pk=skill_id, user=request.user)
    skill.delete()
    messages.info(request, "Skill deleted.")
    return redirect("profile")


@login_required
def skill_listings(request: HttpRequest) -> HttpResponse:
    q = (request.GET.get("q") or "").strip()

    offered_prefetch = Prefetch(
        "skills",
        queryset=Skill.objects.filter(category=Skill.Category.OFFERED),
        to_attr="offered_skills",
    )

    users = (
        User.objects.exclude(pk=request.user.pk)
        .prefetch_related(offered_prefetch)
        .order_by("full_name")
    )
    if q:
        users = users.filter(
            Q(skills__category=Skill.Category.OFFERED, skills__skill_name__icontains=q)
            | Q(full_name__icontains=q)
        ).distinct()

    return render(request, "users/listings.html", {"users": users, "q": q})


@login_required
@require_http_methods(["GET", "POST"])
def swap_request_create(request: HttpRequest, receiver_id: int) -> HttpResponse:
    receiver = get_object_or_404(User, pk=receiver_id)
    if receiver.pk == request.user.pk:
        messages.error(request, "You cannot request a swap with yourself.")
        return redirect("skill_listings")

    offered_skills = list(
        request.user.skills.filter(category=Skill.Category.OFFERED).order_by("skill_name").values_list("skill_name", flat=True)
    )
    requested_skills = list(
        receiver.skills.filter(category=Skill.Category.OFFERED).order_by("skill_name").values_list("skill_name", flat=True)
    )

    offered_choices = [("", "— Select —")] + [(s, s) for s in offered_skills]
    requested_choices = [("", "— Select —")] + [(s, s) for s in requested_skills]

    form = SwapRequestCreateForm(
        request.POST or None, offered_choices=offered_choices, requested_choices=requested_choices
    )

    if request.method == "POST" and form.is_valid():
        skill_offered = form.cleaned_data["skill_offered"]
        skill_requested = form.cleaned_data["skill_requested"]
        if not skill_offered or not skill_requested:
            messages.error(request, "Please choose both skills.")
        else:
            SwapRequest.objects.create(
                sender=request.user,
                receiver=receiver,
                skill_offered=skill_offered,
                skill_requested=skill_requested,
            )
            messages.success(request, "Swap request sent.")
            return redirect("dashboard")

    return render(
        request,
        "swap/request_create.html",
        {
            "receiver": receiver,
            "form": form,
            "offered_count": len(offered_skills),
            "requested_count": len(requested_skills),
        },
    )


@login_required
@require_http_methods(["POST"])
def swap_request_accept(request: HttpRequest, request_id: int) -> HttpResponse:
    swap = get_object_or_404(SwapRequest, pk=request_id, receiver=request.user)
    if swap.status != SwapRequest.Status.PENDING:
        messages.info(request, "This request is already processed.")
        return redirect("dashboard")
    swap.status = SwapRequest.Status.ACCEPTED
    swap.save(update_fields=["status", "updated_at"])
    Conversation.get_or_create_between(swap.sender, swap.receiver)
    messages.success(request, "Request accepted.")
    return redirect("dashboard")


@login_required
@require_http_methods(["POST"])
def swap_request_reject(request: HttpRequest, request_id: int) -> HttpResponse:
    swap = get_object_or_404(SwapRequest, pk=request_id, receiver=request.user)
    if swap.status != SwapRequest.Status.PENDING:
        messages.info(request, "This request is already processed.")
        return redirect("dashboard")
    swap.status = SwapRequest.Status.REJECTED
    swap.save(update_fields=["status", "updated_at"])
    messages.info(request, "Request rejected.")
    return redirect("dashboard")


@login_required
def inbox(request: HttpRequest) -> HttpResponse:
    convos = Conversation.objects.filter(Q(user1=request.user) | Q(user2=request.user)).select_related(
        "user1", "user2"
    )
    # annotate last message quickly by prefetching (simple approach for SQLite scale)
    convos = convos.prefetch_related("messages")
    return render(request, "chat/inbox.html", {"conversations": convos})


@login_required
@require_http_methods(["GET", "POST"])
def conversation_detail(request: HttpRequest, conversation_id: int) -> HttpResponse:
    convo = get_object_or_404(Conversation.objects.select_related("user1", "user2"), pk=conversation_id)
    if not convo.has_user(request.user):
        messages.error(request, "You don't have access to this conversation.")
        return redirect("inbox")

    if request.method == "POST":
        body = (request.POST.get("body") or "").strip()
        if not body:
            messages.error(request, "Message cannot be empty.")
        else:
            Message.objects.create(conversation=convo, sender=request.user, body=body)
            return redirect("conversation_detail", conversation_id=convo.pk)

    msgs = convo.messages.select_related("sender")
    return render(
        request,
        "chat/conversation.html",
        {"conversation": convo, "messages_list": msgs, "other_user": convo.other_user(request.user)},
    )

