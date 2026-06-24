from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg, Count
from django.urls import reverse


class Category(models.Model):
    name = models.CharField("Kategoriya nomi", max_length=100, unique=True)

    class Meta:
        verbose_name = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField("Kitob nomi", max_length=255)
    author = models.CharField("Muallif", max_length=150)
    published_year = models.PositiveIntegerField("Chop etilgan yil")
    description = models.TextField("Tavsif", blank=True)
    cover = models.FileField(
        "Muqova rasmi",
        upload_to="books/",
        blank=True,
        null=True,
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"])],
        help_text="Katalog kartochkasi uchun vertikal rasm. Bo'lmasa banner fallback sifatida ishlaydi.",
    )
    banner = models.FileField(
        "Banner rasmi",
        upload_to="book_banners/",
        blank=False,
        null=True,
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"])],
        help_text="Majburiy. Kitob detail/reader sahifasidagi keng banner rasmi.",
    )
    pdf_file = models.FileField(
        "PDF kitob",
        upload_to="book_pdfs/",
        blank=False,
        null=True,
        validators=[FileExtensionValidator(["pdf"])],
        help_text="Majburiy. PDF yuklanmasa kitob saqlanmaydi.",
    )
    category = models.ForeignKey(
        Category,
        verbose_name="Kategoriya",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="books",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Qo'shgan admin",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="books",
    )
    created_at = models.DateTimeField("Qo'shilgan vaqt", auto_now_add=True)
    updated_at = models.DateTimeField("Yangilangan vaqt", auto_now=True)
    views_count = models.PositiveIntegerField("Ko'rishlar soni", default=0)
    reads_count = models.PositiveIntegerField("O'qishlar soni", default=0)
    downloads_count = models.PositiveIntegerField("Yuklab olishlar", default=0)
    is_featured = models.BooleanField("Tavsiya etilgan", default=False)

    class Meta:
        verbose_name = "Kitob"
        verbose_name_plural = "Kitoblar"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["author"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        errors = {}
        if not self.banner:
            errors["banner"] = "Kitob banner rasmi majburiy."
        if not self.pdf_file:
            errors["pdf_file"] = "PDF fayl majburiy. PDF yuklanmasa kitob saqlanmaydi."
        if errors:
            raise ValidationError(errors)

    def get_absolute_url(self):
        return reverse("book_detail", kwargs={"pk": self.pk})

    @property
    def has_pdf(self):
        return bool(self.pdf_file)

    @property
    def card_image(self):
        return self.cover or self.banner

    @property
    def average_rating(self):
        value = self.reviews.filter(is_approved=True).aggregate(avg=Avg("rating"))["avg"]
        return round(value or 0, 1)

    @property
    def review_count(self):
        return self.reviews.filter(is_approved=True).count()


class BookReview(models.Model):
    RATING_CHOICES = [(i, f"{i} yulduz") for i in range(1, 6)]

    book = models.ForeignKey(Book, verbose_name="Kitob", on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="Foydalanuvchi", on_delete=models.CASCADE, related_name="book_reviews")
    rating = models.PositiveSmallIntegerField(
        "Baho",
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    comment = models.TextField("Izoh", max_length=1200)
    is_approved = models.BooleanField("Ko'rinadi", default=True)
    created_at = models.DateTimeField("Yozilgan vaqt", auto_now_add=True)
    updated_at = models.DateTimeField("Yangilangan vaqt", auto_now=True)

    class Meta:
        verbose_name = "Baho va izoh"
        verbose_name_plural = "Baholar va izohlar"
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(fields=["book", "user"], name="unique_review_per_user_book"),
        ]
        indexes = [
            models.Index(fields=["book", "is_approved"]),
            models.Index(fields=["rating"]),
            models.Index(fields=["-updated_at"]),
        ]

    def __str__(self):
        return f"{self.book} — {self.user} — {self.rating}/5"

    @property
    def user_display(self):
        profile = getattr(self.user, "profile", None)
        if profile and profile.display_name:
            return profile.display_name
        full_name = self.user.get_full_name()
        return full_name or self.user.username

from django.db import models
from django.contrib.auth.models import User


class BookClub(models.Model):
    name = models.CharField("Klub nomi", max_length=255)
    description = models.TextField("Tavsif", blank=True)
    cover = models.ImageField(
        "Klub muqovasi",
        upload_to="club_covers/",
        null=True,
        blank=True,
        help_text="Klub sahifasidagi asosiy rasm. Bo'lmasa default ko'rinadi.",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Egasi",
        on_delete=models.CASCADE,
        related_name="owned_clubs",
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        verbose_name="A'zolar",
        related_name="clubs",
        blank=True,
    )
    admins = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        verbose_name="Adminlar",
        related_name="admin_clubs",
        blank=True,
    )
    is_public = models.BooleanField("Ochiq klub", default=True)
    created_at = models.DateTimeField("Yaratilgan vaqt", auto_now_add=True)

    class Meta:
        verbose_name = "Kitob klubi"
        verbose_name_plural = "Kitob klublari"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    @property
    def member_count(self):
        return self.members.count()

    @property
    def admin_count(self):
        return self.admins.count()

    def is_member(self, user):
        return self.members.filter(pk=user.pk).exists()

    def is_admin(self, user):
        return self.admins.filter(pk=user.pk).exists() or self.owner == user

    def get_absolute_url(self):
        return reverse("club_detail", kwargs={"pk": self.pk})


class ClubMessage(models.Model):
    club = models.ForeignKey(BookClub, verbose_name="Klub", on_delete=models.CASCADE, related_name="messages")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="Foydalanuvchi", on_delete=models.CASCADE)
    message = models.TextField("Xabar")
    created_at = models.DateTimeField("Vaqt", auto_now_add=True)

    class Meta:
        verbose_name = "Xabar"
        verbose_name_plural = "Xabarlar"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.user} → {self.club}: {self.message[:40]}"


class ClubRule(models.Model):
    club = models.ForeignKey(BookClub, verbose_name="Klub", on_delete=models.CASCADE, related_name="rules")
    text = models.TextField("Qoida matni")
    order = models.PositiveSmallIntegerField("Tartib", default=0)

    class Meta:
        verbose_name = "Qoida"
        verbose_name_plural = "Qoidalar"
        ordering = ["order"]

    def __str__(self):
        return f"{self.club.name} — qoida {self.order}"


class ClubReadingPlan(models.Model):
    club = models.ForeignKey(BookClub, verbose_name="Klub", on_delete=models.CASCADE, related_name="reading_plans")
    book = models.ForeignKey(
        Book,
        verbose_name="Kitob",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="club_plans",
    )
    # Agar kitob katalogda bo'lmasa, qo'lda kiritish uchun:
    title = models.CharField("Kitob nomi (qo'lda)", max_length=255, blank=True)
    cover = models.ImageField("Muqova", upload_to="club_books/", null=True, blank=True)
    start_date = models.DateField("Boshlanish sanasi")
    end_date = models.DateField("Tugash sanasi")
    start_page = models.PositiveIntegerField("Boshlanish sahifasi", default=1)
    end_page = models.PositiveIntegerField("Tugash sahifasi", default=0)
    is_active = models.BooleanField("Joriy o'qish", default=True)
    week_number = models.PositiveSmallIntegerField("Hafta raqami", default=1)
    total_weeks = models.PositiveSmallIntegerField("Jami haftalar", default=8)

    class Meta:
        verbose_name = "O'qish rejasi"
        verbose_name_plural = "O'qish rejalari"
        ordering = ["-is_active", "start_date"]

    def __str__(self):
        book_name = self.book.title if self.book else self.title
        return f"{self.club.name} — {book_name}"

    @property
    def display_title(self):
        if self.book:
            return self.book.title
        return self.title

    @property
    def display_cover(self):
        if self.book and self.book.cover:
            return self.book.cover
        return self.cover

    @property
    def progress_percent(self):
        total = self.end_page - self.start_page
        if total <= 0:
            return 0
        from django.utils import timezone
        today = timezone.now().date()
        if today < self.start_date:
            return 0
        if today > self.end_date:
            return 100
        elapsed = (today - self.start_date).days
        total_days = (self.end_date - self.start_date).days or 1
        return min(int((elapsed / total_days) * 100), 100)
