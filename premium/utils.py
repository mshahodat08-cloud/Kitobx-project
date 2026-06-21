"""Kichik yordamchi funksiyalar: bildirishnoma yaratish va h.k."""


def notify(user, title, message, icon="bell", link=""):
    """Foydalanuvchiga yangi bildirishnoma yaratadi."""
    from .models import Notification

    if not user or not getattr(user, "is_authenticated", False):
        return None
    return Notification.objects.create(
        user=user,
        title=title,
        message=message,
        icon=icon,
        link=link,
    )
