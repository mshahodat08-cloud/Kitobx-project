from django.conf import settings
from django.db import models

from books.models import Book


# ---------------------------------------------------------------------------
# Wishlist
# ---------------------------------------------------------------------------
class Wishlist(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Foydalanuvchi",
        on_delete=models.CASCADE,
        related_name="wishlist_items",
    )
    book = models.ForeignKey(
        Book,
        verbose_name="Kitob",
        on_delete=models.CASCADE,
        related_name="wishlisted_by",
    )
    created_at = models.DateTimeField("Qo'shilgan vaqt", auto_now_add=True)

    class Meta:
        verbose_name = "Sevimli kitob"
        verbose_name_plural = "❤ Wishlist"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "book"], name="unique_wishlist_user_book"),
        ]

    def __str__(self):
        return f"{self.user} ♥ {self.book}"


# ---------------------------------------------------------------------------
# Reading progress + history
# ---------------------------------------------------------------------------
class ReadingProgress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Foydalanuvchi",
        on_delete=models.CASCADE,
        related_name="reading_progresses",
    )
    book = models.ForeignKey(
        Book,
        verbose_name="Kitob",
        on_delete=models.CASCADE,
        related_name="reading_progresses",
    )
    percent = models.PositiveSmallIntegerField("Progress (%)", default=0)
    is_completed = models.BooleanField("Tugatilgan", default=False)
    started_at = models.DateTimeField("Boshlangan vaqt", auto_now_add=True)
    updated_at = models.DateTimeField("Yangilangan vaqt", auto_now=True)
    completed_at = models.DateTimeField("Tugatilgan vaqt", null=True, blank=True)

    class Meta:
        verbose_name = "O'qish jarayoni"
        verbose_name_plural = "📖 O'qish jarayonlari"
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "book"], name="unique_progress_user_book"),
        ]

    def __str__(self):
        return f"{self.user} — {self.book} — {self.percent}%"


class ReadingHistory(models.Model):
    ACTION_CHOICES = [
        ("started", "Boshlandi"),
        ("continued", "Davom etildi"),
        ("completed", "Tugatildi"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Foydalanuvchi",
        on_delete=models.CASCADE,
        related_name="reading_history",
    )
    book = models.ForeignKey(
        Book,
        verbose_name="Kitob",
        on_delete=models.CASCADE,
        related_name="history_entries",
    )
    action = models.CharField("Harakat", max_length=12, choices=ACTION_CHOICES, default="continued")
    percent_at_event = models.PositiveSmallIntegerField("O'sha damdagi progress", default=0)
    created_at = models.DateTimeField("Vaqt", auto_now_add=True)

    class Meta:
        verbose_name = "Tarix yozuvi"
        verbose_name_plural = "📚 O'qish tarixi"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "-created_at"])]

    def __str__(self):
        return f"{self.user} — {self.book} — {self.get_action_display()}"


# ---------------------------------------------------------------------------
# Reading challenge
# ---------------------------------------------------------------------------
class ReadingChallenge(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Foydalanuvchi",
        on_delete=models.CASCADE,
        related_name="reading_challenges",
    )
    year = models.PositiveIntegerField("Yil")
    goal = models.PositiveIntegerField("Maqsad (kitoblar soni)", default=12)
    created_at = models.DateTimeField("Yaratilgan vaqt", auto_now_add=True)
    updated_at = models.DateTimeField("Yangilangan vaqt", auto_now=True)

    class Meta:
        verbose_name = "O'qish marafoni"
        verbose_name_plural = "🎯 O'qish marafonlari"
        ordering = ["-year"]
        constraints = [
            models.UniqueConstraint(fields=["user", "year"], name="unique_challenge_user_year"),
        ]

    def __str__(self):
        return f"{self.user} — {self.year} — {self.goal} kitob"

    @property
    def completed_count(self):
        return ReadingHistory.objects.filter(
            user=self.user, action="completed", created_at__year=self.year
        ).values("book_id").distinct().count()

    @property
    def progress_percent(self):
        if not self.goal:
            return 0
        return min(100, round(self.completed_count * 100 / self.goal))

    @property
    def is_achieved(self):
        return self.completed_count >= self.goal


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------
class Notification(models.Model):
    ICON_CHOICES = [
        ("bell", "Bell"),
        ("check", "Check"),
        ("crown", "Crown"),
        ("heart", "Heart"),
        ("target", "Target"),
        ("sparkles", "Sparkles"),
        ("star", "Star"),
        ("book", "Book"),
        ("alert", "Alert"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Foydalanuvchi",
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    title = models.CharField("Sarlavha", max_length=160)
    message = models.CharField("Xabar", max_length=300)
    icon = models.CharField("Ikonka", max_length=20, choices=ICON_CHOICES, default="bell")
    link = models.CharField("Havola", max_length=300, blank=True)
    is_read = models.BooleanField("O'qilgan", default=False)
    created_at = models.DateTimeField("Vaqt", auto_now_add=True)

    class Meta:
        verbose_name = "Bildirishnoma"
        verbose_name_plural = "🔔 Bildirishnomalar"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "is_read"])]

    def __str__(self):
        return f"{self.user} — {self.title}"


# ---------------------------------------------------------------------------
# VIP subscription
# ---------------------------------------------------------------------------
class VIPPlan(models.Model):
    name = models.CharField("Reja nomi", max_length=80)
    slug = models.SlugField("Slug", max_length=80, unique=True)
    tagline = models.CharField("Qisqa tavsif", max_length=160, blank=True)
    price = models.DecimalField("Narx (so'm)", max_digits=12, decimal_places=0)
    duration_days = models.PositiveIntegerField("Muddati (kun)", default=30, help_text="0 = cheksiz")
    features = models.TextField("Imkoniyatlar", help_text="Har bir qatorda bitta imkoniyat.")
    is_popular = models.BooleanField("Mashhur reja", default=False)
    sort_order = models.PositiveIntegerField("Tartib", default=0)

    class Meta:
        verbose_name = "VIP reja"
        verbose_name_plural = "👑 VIP rejalar"
        ordering = ["sort_order", "price"]

    def __str__(self):
        return self.name

    @property
    def feature_list(self):
        return [line.strip() for line in self.features.splitlines() if line.strip()]


class VIPTransaction(models.Model):
    STATUS_CHOICES = [("success", "Muvaffaqiyatli"), ("failed", "Xato")]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Foydalanuvchi",
        on_delete=models.CASCADE,
        related_name="vip_transactions",
    )
    plan = models.ForeignKey(VIPPlan, verbose_name="Reja", on_delete=models.SET_NULL, null=True, related_name="transactions")
    amount = models.DecimalField("Summa", max_digits=12, decimal_places=0)
    status = models.CharField("Holat", max_length=10, choices=STATUS_CHOICES, default="success")
    expires_at = models.DateTimeField("Tugash vaqti", null=True, blank=True)
    created_at = models.DateTimeField("Vaqt", auto_now_add=True)

    class Meta:
        verbose_name = "VIP to'lov"
        verbose_name_plural = "💳 VIP to'lovlar"
        ordering = ["-created_at"]

    def __str__(self):
        plan_name = self.plan.name if self.plan else "—"
        return f"{self.user} — {plan_name} — {self.amount}"


# ---------------------------------------------------------------------------
# AI chatbot
# ---------------------------------------------------------------------------
class ChatMessage(models.Model):
    ROLE_CHOICES = [("user", "Foydalanuvchi"), ("assistant", "AI yordamchi")]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Foydalanuvchi",
        on_delete=models.CASCADE,
        related_name="chat_messages",
        null=True,
        blank=True,
    )
    session_key = models.CharField("Sessiya", max_length=64, blank=True)
    role = models.CharField("Rol", max_length=10, choices=ROLE_CHOICES)
    content = models.TextField("Matn")
    created_at = models.DateTimeField("Vaqt", auto_now_add=True)

    class Meta:
        verbose_name = "AI suhbat xabari"
        verbose_name_plural = "🤖 AI suhbat xabarlari"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.get_role_display()}: {self.content[:40]}"
