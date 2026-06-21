from datetime import timedelta

from django import template
from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.utils import timezone

from accounts.models import Profile
from books.models import Book, BookReview, Category

register = template.Library()


def _date_labels(days=7):
    today = timezone.localdate()
    dates = [today - timedelta(days=offset) for offset in range(days - 1, -1, -1)]
    labels = [d.strftime("%d.%m") for d in dates]
    return today, dates, labels


@register.simple_tag
def admin_total_books():
    return Book.objects.count()


@register.simple_tag
def admin_total_categories():
    return Category.objects.count()


@register.simple_tag
def admin_total_users():
    User = get_user_model()
    return User.objects.count()


@register.simple_tag
def admin_total_views():
    return Book.objects.aggregate(total=Sum("views_count")).get("total") or 0


@register.simple_tag
def admin_total_reads():
    return Book.objects.aggregate(total=Sum("reads_count")).get("total") or 0


@register.simple_tag
def admin_total_downloads():
    return Book.objects.aggregate(total=Sum("downloads_count")).get("total") or 0


@register.simple_tag
def admin_total_reviews():
    return BookReview.objects.count()


@register.simple_tag
def admin_approved_reviews():
    return BookReview.objects.filter(is_approved=True).count()


@register.simple_tag
def admin_pdf_books():
    return Book.objects.exclude(pdf_file="").exclude(pdf_file__isnull=True).count()


@register.simple_tag
def admin_vip_users():
    return Profile.objects.filter(is_vip=True).count()


@register.simple_tag
def admin_latest_books(limit=6):
    return Book.objects.select_related("category", "created_by").order_by("-created_at")[:limit]


@register.simple_tag
def admin_latest_users(limit=6):
    User = get_user_model()
    return User.objects.select_related("profile").order_by("-date_joined")[:limit]


@register.simple_tag
def admin_top_categories(limit=6):
    return Category.objects.annotate(total_books=Count("books")).order_by("-total_books", "name")[:limit]


@register.simple_tag
def admin_top_books(limit=6):
    return Book.objects.select_related("category").order_by("-reads_count", "-views_count", "title")[:limit]


@register.simple_tag
def admin_dashboard_payload():
    User = get_user_model()
    today, dates, labels = _date_labels(7)

    total_books = Book.objects.count()
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    staff_users = User.objects.filter(is_staff=True).count()
    vip_users = Profile.objects.filter(is_vip=True).count()
    pdf_books = Book.objects.exclude(pdf_file="").exclude(pdf_file__isnull=True).count()
    total_views = Book.objects.aggregate(total=Sum("views_count")).get("total") or 0
    total_reads = Book.objects.aggregate(total=Sum("reads_count")).get("total") or 0
    total_downloads = Book.objects.aggregate(total=Sum("downloads_count")).get("total") or 0
    avg_reads = round(total_reads / total_books, 1) if total_books else 0

    week_start = today - timedelta(days=6)
    users_by_day = []
    books_by_day = []
    for current_date in dates:
        users_by_day.append(User.objects.filter(date_joined__date=current_date).count())
        books_by_day.append(Book.objects.filter(created_at__date=current_date).count())

    categories = list(
        Category.objects.annotate(total_books=Count("books"))
        .order_by("-total_books", "name")[:6]
        .values("name", "total_books")
    )
    if not categories:
        categories = [{"name": "Ma'lumot yo'q", "total_books": 0}]

    top_books = list(
        Book.objects.order_by("-reads_count", "-views_count", "title")[:7]
        .values("title", "reads_count", "views_count")
    )
    if not top_books:
        top_books = [{"title": "Ma'lumot yo'q", "reads_count": 0, "views_count": 0}]

    return {
        "metrics": {
            "books": total_books,
            "users": total_users,
            "activeUsers": active_users,
            "staffUsers": staff_users,
            "vipUsers": vip_users,
            "pdfBooks": pdf_books,
            "views": total_views,
            "reads": total_reads,
            "downloads": total_downloads,
            "avgReads": avg_reads,
            "newUsersWeek": User.objects.filter(date_joined__date__gte=week_start).count(),
            "newBooksWeek": Book.objects.filter(created_at__date__gte=week_start).count(),
            "todayUsers": User.objects.filter(date_joined__date=today).count(),
            "todayBooks": Book.objects.filter(created_at__date=today).count(),
        },
        "growth": {"labels": labels, "users": users_by_day, "books": books_by_day},
        "categories": {
            "labels": [item["name"] for item in categories],
            "values": [item["total_books"] for item in categories],
        },
        "topBooks": {
            "labels": [item["title"] for item in top_books],
            "reads": [item["reads_count"] for item in top_books],
            "views": [item["views_count"] for item in top_books],
        },
    }

@register.simple_tag
def admin_active_users():
    User = get_user_model()
    return User.objects.filter(is_active=True).count()


@register.simple_tag
def admin_percent(part, total):
    try:
        part = float(part or 0)
        total = float(total or 0)
        if total <= 0:
            return 0
        return max(0, min(100, round((part / total) * 100)))
    except (TypeError, ValueError, ZeroDivisionError):
        return 0
