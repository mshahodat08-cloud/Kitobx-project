from .models import Notification, Wishlist


def premium_context(request):
    """base.html uchun bildirishnomalar, wishlist va boshqa global ma'lumotlar."""
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {
            "nav_notifications": [],
            "nav_unread_count": 0,
            "nav_wishlist_ids": set(),
        }

    notifications = list(Notification.objects.filter(user=user)[:8])
    unread_count = Notification.objects.filter(user=user, is_read=False).count()
    wishlist_ids = set(Wishlist.objects.filter(user=user).values_list("book_id", flat=True))

    return {
        "nav_notifications": notifications,
        "nav_unread_count": unread_count,
        "nav_wishlist_ids": wishlist_ids,
    }
