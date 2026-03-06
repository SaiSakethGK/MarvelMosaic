"""
Views for Marvel Mosaic.

Author: Sai Saketh Gooty Kase
"""

import logging

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views import View

from .forms import SignUpForm
from .models import FavoriteCharacter, Post, Reply
from marvel_api import get_character_by_id, get_marvel_characters

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _send_zapier(payload: dict) -> None:
    """Fire-and-forget POST to the configured Zapier webhook."""
    url = settings.ZAPIER_WEBHOOK_URL
    if not url:
        return
    try:
        requests.post(url, json=payload, timeout=5)
    except requests.exceptions.RequestException as exc:
        logger.warning("Zapier webhook failed: %s", exc)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def home(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {username}!")
            return redirect("home")
        messages.error(request, "Invalid username or password.")
        return redirect("home")
    return render(request, "home.html")


def logout_user(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("home")


def register_user(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password1"]
            user = authenticate(username=username, password=password)
            login(request, user)

            if form.cleaned_data.get("subscribe_news"):
                user.profile.subscribe_news = True
                user.profile.save()
                _send_zapier({
                    "email": user.email,
                    "name": f"{user.first_name} {user.last_name}".strip(),
                    "type": "welcome",
                })

            messages.success(request, "Account created — welcome to Marvel Mosaic!")
            return redirect("home")
    else:
        form = SignUpForm()
    return render(request, "register.html", {"form": form})


# ---------------------------------------------------------------------------
# Characters
# ---------------------------------------------------------------------------

@login_required
def characters_list(request):
    search_query = request.GET.get("search", "").strip()
    characters = get_marvel_characters()

    if search_query:
        characters = [
            c for c in characters
            if search_query.lower() in c["name"].lower()
        ]

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        html = render_to_string(
            "characters_list_partial.html",
            {"characters": characters},
            request=request,
        )
        return JsonResponse({"characters_html": html})

    return render(request, "characters_list.html", {"characters": characters})


def character_detail(request, character_id):
    character = get_character_by_id(character_id)
    if not character:
        messages.error(request, "Character not found.")
        return redirect("characters_list")

    posts = Post.objects.filter(
        character_id=character_id
    ).select_related("user").prefetch_related("replies__user").order_by("-created_at")

    return render(request, "character_detail.html", {
        "character": character,
        "posts": posts,
    })


# ---------------------------------------------------------------------------
# Favorites
# ---------------------------------------------------------------------------

@login_required
def add_to_favorites(request, character_id):
    _, created = FavoriteCharacter.objects.get_or_create(
        user=request.user,
        character_id=character_id,
    )
    if created:
        messages.success(request, "Character added to favorites!")
    else:
        messages.info(request, "Already in your favorites.")
    return redirect("character_detail", character_id=character_id)


@login_required
def view_favorites(request):
    favorites = (
        FavoriteCharacter.objects
        .filter(user=request.user)
        .order_by("rank", "id")
    )
    characters_data = []
    for fav in favorites:
        character = get_character_by_id(fav.character_id)
        if character:
            thumb = character.get("thumbnail", {})
            characters_data.append({
                "id": fav.character_id,
                "name": character["name"],
                "image_url": f"{thumb.get('path', '')}.{thumb.get('extension', '')}",
                "rank": fav.rank,
            })

    return render(request, "favorites.html", {
        "characters_data": characters_data,
        "no_characters_found": not characters_data,
        "range": list(range(1, len(favorites) + 1)),
    })


@login_required
def update_rank(request, character_id):
    fav = get_object_or_404(FavoriteCharacter, user=request.user, character_id=character_id)
    if request.method == "POST":
        try:
            new_rank = int(request.POST.get("rank", 0))
            fav.rank = new_rank
            fav.save(update_fields=["rank"])
        except (ValueError, TypeError):
            messages.error(request, "Invalid rank value.")
    return redirect("view_favorites")


def confirm_remove_from_favorites(request, character_id):
    character = get_character_by_id(character_id)
    return render(request, "confirm_remove.html", {"character": character})


@method_decorator(login_required, name="dispatch")
class RemoveFromFavoritesView(View):
    def post(self, request, character_id):
        fav = FavoriteCharacter.objects.filter(
            user=request.user,
            character_id=character_id,
        ).first()

        if fav:
            character = get_character_by_id(character_id)
            name = character["name"] if character else f"Character #{character_id}"
            fav.delete()
            messages.success(request, f"{name} removed from favorites.")
        else:
            messages.info(request, "Character was not in your favorites.")

        return redirect("view_favorites")


# ---------------------------------------------------------------------------
# Discussion
# ---------------------------------------------------------------------------

@login_required
def create_post(request, character_id):
    if request.method == "POST":
        content = request.POST.get("content", "").strip()
        if content:
            Post.objects.create(
                user=request.user,
                character_id=character_id,
                content=content,
            )
    return redirect("character_detail", character_id=character_id)


@login_required
def create_reply(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == "POST":
        content = request.POST.get("content", "").strip()
        if content:
            Reply.objects.create(user=request.user, post=post, content=content)
    return redirect("character_detail", character_id=post.character_id)


# ---------------------------------------------------------------------------
# Internal API endpoints
# ---------------------------------------------------------------------------

@login_required
def trigger_morning_email(request):
    """Send a morning update webhook to all subscribed users."""
    users = User.objects.filter(profile__subscribe_news=True)
    for user in users:
        _send_zapier({
            "email": user.email,
            "name": f"{user.first_name} {user.last_name}".strip(),
            "type": "morning",
        })
    logger.info("Morning email triggered for %d users", users.count())
    return JsonResponse({"status": "ok", "recipients": users.count()})


def subscribed_emails(request):
    emails = list(
        User.objects.filter(profile__subscribe_news=True)
        .values_list("email", flat=True)
    )
    return JsonResponse({"emails": emails})


def get_subscribed_users(request):
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    users = User.objects.filter(profile__subscribe_news=True)
    data = [
        {"email": u.email, "name": f"{u.first_name} {u.last_name}".strip()}
        for u in users
    ]
    return JsonResponse({"users": data})
