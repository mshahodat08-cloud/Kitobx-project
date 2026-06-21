"""👑 AI Recommendation — kontent va xulq-atvorga asoslangan tavsiya tizimi.

Tizim foydalanuvchining o'qish tarixi, wishlist va baholarini tahlil qilib,
mos kategoriyadagi eng yuqori baholangan va mashhur kitoblarni taklif qiladi.
Hisob-kitob to'liq lokal bo'lib, tashqi API yoki kalit talab qilmaydi.
"""
from django.db.models import Avg, Count, Q

from books.models import Book


def _scored_queryset():
    return Book.objects.select_related("category").annotate(
        avg_rating=Avg("reviews__rating", filter=Q(reviews__is_approved=True)),
        reviews_total=Count("reviews", filter=Q(reviews__is_approved=True)),
    )


def get_recommendations(user, limit=8):
    """Foydalanuvchi uchun tavsiya etilgan kitoblar ro'yxatini qaytaradi.

    Har bir kitobga ``reco_reason`` matni biriktiriladi — UI'da ko'rsatish uchun.
    """
    qs = _scored_queryset()

    if not user or not user.is_authenticated:
        trending = list(qs.order_by("-is_featured", "-views_count", "-avg_rating")[:limit])
        for book in trending:
            book.reco_reason = "Platformada eng ko'p o'qilayotgan kitob"
        return trending

    from .models import ReadingHistory, Wishlist

    interacted_ids = set(
        ReadingHistory.objects.filter(user=user).values_list("book_id", flat=True)
    ) | set(
        Wishlist.objects.filter(user=user).values_list("book_id", flat=True)
    )

    liked_category_ids = list(
        Book.objects.filter(id__in=interacted_ids)
        .exclude(category__isnull=True)
        .values_list("category_id", flat=True)
        .distinct()
    )
    category_names = {}
    if liked_category_ids:
        from books.models import Category

        category_names = {c.id: c.name for c in Category.objects.filter(id__in=liked_category_ids)}

    recommendations = []
    seen_ids = set()

    if liked_category_ids:
        by_category = (
            qs.filter(category_id__in=liked_category_ids)
            .exclude(id__in=interacted_ids)
            .order_by("-avg_rating", "-reviews_total", "-views_count")
        )
        for book in by_category:
            if book.id in seen_ids:
                continue
            cat_name = category_names.get(book.category_id, "")
            book.reco_reason = (
                f"\"{cat_name}\" kategoriyasini yoqtirganingiz uchun tavsiya qilindi" if cat_name
                else "Sizning didingizga mos kitob"
            )
            recommendations.append(book)
            seen_ids.add(book.id)
            if len(recommendations) >= limit:
                break

    if len(recommendations) < limit:
        top_rated = (
            qs.exclude(id__in=interacted_ids | seen_ids)
            .order_by("-avg_rating", "-views_count")
        )
        for book in top_rated:
            if book.id in seen_ids:
                continue
            book.reco_reason = "Yuqori baholangan, sinab ko'rishingiz mumkin"
            recommendations.append(book)
            seen_ids.add(book.id)
            if len(recommendations) >= limit:
                break

    return recommendations[:limit]
