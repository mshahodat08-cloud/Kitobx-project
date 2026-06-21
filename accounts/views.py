from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from books.models import Book

from .forms import LoginForm, ProfileUpdateForm, RegisterForm, UserUpdateForm
from .models import Profile
from premium.utils import notify


def get_profile(user):
    profile, _ = Profile.objects.get_or_create(user=user)
    return profile


def register_view(request):
    if request.user.is_authenticated:
        return redirect("profile")

    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        Profile.objects.get_or_create(user=user)
        login(request, user)
        notify(
            user,
            "KitobX'ga xush kelibsiz! 👋",
            "Wishlist, AI tavsiyalar va Reading Challenge kabi imkoniyatlarni sinab ko'ring.",
            icon="sparkles",
            link="/tavsiyalar/",
        )
        messages.success(request, "Ro'yxatdan o'tish muvaffaqiyatli yakunlandi.")
        return redirect("profile")

    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("profile")

    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        messages.success(request, "Tizimga muvaffaqiyatli kirdingiz.")
        next_url = request.GET.get("next")
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            return redirect(next_url)
        return redirect("book_list")

    return render(request, "accounts/login.html", {"form": form})


@login_required
def logout_view(request):
    if request.method == "POST":
        logout(request)
        messages.success(request, "Tizimdan chiqdingiz.")
        return redirect("book_list")
    return render(request, "accounts/logout_confirm.html")


@login_required
def profile_view(request):
    profile = get_profile(request.user)
    my_books = Book.objects.filter(created_by=request.user).select_related("category")[:6]

    from premium.models import ReadingChallenge, ReadingHistory, Wishlist
    from django.utils import timezone

    challenge, _ = ReadingChallenge.objects.get_or_create(user=request.user, year=timezone.now().year)
    context = {
        "profile": profile,
        "my_books": my_books,
        "my_books_count": Book.objects.filter(created_by=request.user).count(),
        "total_books": Book.objects.count(),
        "total_views": Book.objects.aggregate(total=Sum("views_count"))["total"] or 0,
        "pdf_books_count": Book.objects.exclude(pdf_file="").exclude(pdf_file__isnull=True).count(),
        "vip_required": not profile.is_vip_active,
        "wishlist_count": Wishlist.objects.filter(user=request.user).count(),
        "completed_books_count": ReadingHistory.objects.filter(user=request.user, action="completed").values("book_id").distinct().count(),
        "challenge": challenge,
    }
    return render(request, "accounts/profile.html", context)


@login_required
def profile_edit_view(request):
    profile = get_profile(request.user)
    user_form = UserUpdateForm(request.POST or None, instance=request.user)
    profile_form = ProfileUpdateForm(request.POST or None, request.FILES or None, instance=profile)

    if request.method == "POST" and user_form.is_valid() and profile_form.is_valid():
        user_form.save()
        profile_form.save()
        messages.success(request, "Profil ma'lumotlari yangilandi.")
        return redirect("profile")

    return render(
        request,
        "accounts/profile_edit.html",
        {"user_form": user_form, "profile_form": profile_form, "profile": profile},
    )
