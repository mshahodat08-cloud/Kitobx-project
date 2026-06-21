import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from books.models import Book

from .chatbot import generate_reply
from .models import (
    ChatMessage,
    Notification,
    ReadingChallenge,
    ReadingHistory,
    ReadingProgress,
    VIPPlan,
    VIPTransaction,
    Wishlist,
)
from .recommend import get_recommendations
from .utils import notify


def _is_ajax(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest" or "application/json" in request.headers.get("accept", "")


# ---------------------------------------------------------------------------
# ❤ Wishlist
# ---------------------------------------------------------------------------
@login_required
def wishlist_view(request):
    items = Wishlist.objects.filter(user=request.user).select_related("book", "book__category")
    return render(request, "premium/wishlist.html", {"items": items})


@login_required
@require_POST
def wishlist_toggle(request, pk):
    book = get_object_or_404(Book, pk=pk)
    item = Wishlist.objects.filter(user=request.user, book=book).first()
    if item:
        item.delete()
        added = False
    else:
        Wishlist.objects.create(user=request.user, book=book)
        added = True

    if _is_ajax(request):
        return JsonResponse({
            "added": added,
            "count": Wishlist.objects.filter(user=request.user).count(),
        })

    messages.success(request, "Wishlistga qo'shildi." if added else "Wishlistdan olib tashlandi.")
    return redirect(request.META.get("HTTP_REFERER") or "book_list")


# ---------------------------------------------------------------------------
# 📖 Reading progress + 📚 history
# ---------------------------------------------------------------------------
@login_required
def reading_history_view(request):
    history = ReadingHistory.objects.filter(user=request.user).select_related("book", "book__category")[:150]
    progresses = {
        p.book_id: p
        for p in ReadingProgress.objects.filter(user=request.user).select_related("book")
    }
    return render(request, "premium/history.html", {"history": history, "progresses": progresses})


@login_required
@require_POST
def update_progress(request, pk):
    book = get_object_or_404(Book, pk=pk)
    try:
        data = json.loads(request.body or "{}")
    except (json.JSONDecodeError, TypeError):
        data = {}
    try:
        percent = int(data.get("percent", request.POST.get("percent", 0)))
    except (TypeError, ValueError):
        percent = 0
    percent = max(0, min(100, percent))

    progress, created = ReadingProgress.objects.get_or_create(user=request.user, book=book, defaults={"percent": percent})
    was_completed = progress.is_completed

    if not created:
        progress.percent = max(progress.percent, percent)
    if progress.percent >= 100 and not progress.is_completed:
        progress.is_completed = True
        progress.completed_at = timezone.now()
    progress.save()

    if created:
        ReadingHistory.objects.create(user=request.user, book=book, action="started", percent_at_event=progress.percent)
    elif progress.is_completed and not was_completed:
        ReadingHistory.objects.create(user=request.user, book=book, action="completed", percent_at_event=100)
        notify(
            request.user,
            "Tabriklaymiz! 🎉",
            f"\"{book.title}\" kitobini muvaffaqiyatli tugatdingiz.",
            icon="check",
            link=book.get_absolute_url(),
        )
        challenge, _ = ReadingChallenge.objects.get_or_create(user=request.user, year=timezone.now().year)
        if challenge.is_achieved:
            notify(
                request.user,
                "Reading Challenge yakunlandi! 🏆",
                f"{challenge.year}-yilgi {challenge.goal} kitob maqsadingizga yetdingiz.",
                icon="target",
                link="/challenge/",
            )
    else:
        ReadingHistory.objects.create(user=request.user, book=book, action="continued", percent_at_event=progress.percent)

    return JsonResponse({"percent": progress.percent, "completed": progress.is_completed})


# ---------------------------------------------------------------------------
# 🎯 Reading challenge
# ---------------------------------------------------------------------------
@login_required
def challenge_view(request):
    year = timezone.now().year
    challenge, _ = ReadingChallenge.objects.get_or_create(user=request.user, year=year)

    if request.method == "POST":
        try:
            goal = int(request.POST.get("goal", 12))
        except (TypeError, ValueError):
            goal = 12
        challenge.goal = max(1, min(goal, 365))
        challenge.save(update_fields=["goal", "updated_at"])
        messages.success(request, "Reading Challenge maqsadi yangilandi.")
        return redirect("challenge")

    completed_entries = (
        ReadingHistory.objects.filter(user=request.user, action="completed", created_at__year=year)
        .select_related("book")
        .order_by("-created_at")
    )
    history_by_year = (
        ReadingChallenge.objects.filter(user=request.user).exclude(year=year).order_by("-year")
    )
    return render(
        request,
        "premium/challenge.html",
        {
            "challenge": challenge,
            "completed_entries": completed_entries,
            "previous_challenges": history_by_year,
        },
    )


# ---------------------------------------------------------------------------
# 🤖 AI Recommendation
# ---------------------------------------------------------------------------
def recommendations_view(request):
    recs = get_recommendations(request.user if request.user.is_authenticated else None, limit=12)
    return render(request, "premium/recommendations.html", {"recommendations": recs})


# ---------------------------------------------------------------------------
# 👑 VIP subscription
# ---------------------------------------------------------------------------
def vip_plans_view(request):
    plans = VIPPlan.objects.all()
    transactions = []
    if request.user.is_authenticated:
        transactions = VIPTransaction.objects.filter(user=request.user).select_related("plan")[:5]
    return render(request, "premium/vip_plans.html", {"plans": plans, "transactions": transactions})


@login_required
@require_POST
def vip_subscribe(request, slug):
    plan = get_object_or_404(VIPPlan, slug=slug)
    profile = request.user.profile
    now = timezone.now()

    base = profile.vip_expires_at if (profile.is_vip_active and profile.vip_expires_at) else now
    profile.is_vip = True
    profile.vip_expires_at = None if plan.duration_days == 0 else base + timezone.timedelta(days=plan.duration_days)
    profile.save(update_fields=["is_vip", "vip_expires_at", "updated_at"])

    VIPTransaction.objects.create(
        user=request.user,
        plan=plan,
        amount=plan.price,
        status="success",
        expires_at=profile.vip_expires_at,
    )
    notify(
        request.user,
        "VIP faollashtirildi! 👑",
        f"\"{plan.name}\" rejasi muvaffaqiyatli faollashtirildi. Endi barcha kitoblarni yuklab olishingiz mumkin.",
        icon="crown",
        link="/accounts/profile/",
    )

    if _is_ajax(request):
        return JsonResponse({
            "ok": True,
            "plan": plan.name,
            "is_vip": True,
            "vip_label": profile.vip_label,
        })

    messages.success(request, f"\"{plan.name}\" VIP rejasi faollashtirildi!")
    return redirect("vip_plans")


# ---------------------------------------------------------------------------
# 🔔 Notifications
# ---------------------------------------------------------------------------
@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(user=request.user)
    return render(request, "premium/notifications.html", {"notifications": notifications})


@login_required
@require_POST
def notification_mark_read(request, pk):
    notif = get_object_or_404(Notification, pk=pk, user=request.user)
    notif.is_read = True
    notif.save(update_fields=["is_read"])
    return JsonResponse({"ok": True})


@login_required
@require_POST
def notifications_mark_all_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({"ok": True})


# ---------------------------------------------------------------------------
# 🤖 AI Chatbot
# ---------------------------------------------------------------------------
@require_POST
def chatbot_message(request):
    try:
        data = json.loads(request.body or "{}")
    except (json.JSONDecodeError, TypeError):
        data = {}
    message = (data.get("message") or "").strip()
    if not message:
        return JsonResponse({"reply": "Iltimos, savolingizni yozing.", "books": []})
    if len(message) > 500:
        message = message[:500]

    user = request.user if request.user.is_authenticated else None
    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key

    if user:
        ChatMessage.objects.create(user=user, session_key=session_key, role="user", content=message)

    result = generate_reply(user, message)

    if user:
        ChatMessage.objects.create(user=user, session_key=session_key, role="assistant", content=result.get("reply", ""))

    return JsonResponse(result)
