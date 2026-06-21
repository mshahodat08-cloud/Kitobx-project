from django.conf import settings
from django.db import models
from django.utils import timezone


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    display_name = models.CharField("Ko'rinadigan ism", max_length=120, blank=True)
    phone = models.CharField("Telefon raqam", max_length=32, blank=True)
    bio = models.TextField("Qisqa ma'lumot", blank=True)
    avatar = models.FileField("Profil rasmi", upload_to="profiles/", blank=True, null=True)
    is_vip = models.BooleanField("VIP foydalanuvchi", default=False)
    vip_expires_at = models.DateTimeField("VIP tugash vaqti", blank=True, null=True)
    created_at = models.DateTimeField("Yaratilgan vaqt", auto_now_add=True)
    updated_at = models.DateTimeField("Yangilangan vaqt", auto_now=True)

    class Meta:
        verbose_name = "Profil"
        verbose_name_plural = "Profillar"

    def __str__(self):
        return self.name

    @property
    def name(self):
        return (
            self.display_name
            or self.user.get_full_name()
            or self.user.username
        )

    @property
    def initials(self):
        source = self.name.strip() or self.user.username
        parts = [part for part in source.split() if part]
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        return source[:2].upper()

    @property
    def is_vip_active(self):
        if not self.is_vip:
            return False
        if self.vip_expires_at and self.vip_expires_at < timezone.now():
            return False
        return True

    @property
    def vip_label(self):
        if self.is_vip_active:
            if self.vip_expires_at:
                return f"VIP · {self.vip_expires_at:%d.%m.%Y} gacha"
            return "VIP · cheksiz"
        return "Oddiy hisob"
