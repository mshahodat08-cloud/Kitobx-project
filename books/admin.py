from django.contrib import admin
from django.db.models import Avg, Count, Sum
from django.utils.html import format_html

from .models import Book, BookReview, Category


admin.site.site_header = "KitobX Admin"
admin.site.site_title = "KitobX Admin"
admin.site.index_title = "Platforma boshqaruvi"
admin.site.empty_value_display = "—"


@admin.action(description="Ko'rish / o'qish / download statistikasini reset qilish")
def reset_views(modeladmin, request, queryset):
    queryset.update(views_count=0, reads_count=0, downloads_count=0)


@admin.action(description="Tavsiya etilgan qilish")
def mark_featured(modeladmin, request, queryset):
    queryset.update(is_featured=True)


@admin.action(description="Tavsiyadan olib tashlash")
def unmark_featured(modeladmin, request, queryset):
    queryset.update(is_featured=False)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = (
        "banner_preview",
        "title_block",
        "author",
        "category_badge",
        "rating_badge",
        "pdf_status",
        "featured_badge",
        "reads_badge",
        "downloads_badge",
        "created_at",
    )
    list_display_links = ("banner_preview", "title_block")
    list_filter = ("is_featured", "category", "published_year", "created_at", "created_by")
    search_fields = ("title", "author", "description", "created_by__username")
    readonly_fields = (
        "banner_large_preview",
        "cover_large_preview",
        "pdf_link",
        "rating_summary",
        "created_at",
        "updated_at",
        "views_count",
        "reads_count",
        "downloads_count",
    )
    autocomplete_fields = ("category", "created_by")
    list_select_related = ("category", "created_by")
    list_per_page = 20
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    actions = (reset_views, mark_featured, unmark_featured)
    fieldsets = (
        ("Asosiy ma'lumotlar", {"fields": ("title", "author", "published_year", "category", "is_featured")} ),
        ("Majburiy fayllar", {"fields": ("banner", "banner_large_preview", "pdf_file", "pdf_link")} ),
        ("Qo'shimcha media", {"fields": ("cover", "cover_large_preview")} ),
        ("Tavsif", {"fields": ("description",)}),
        ("Baholar", {"fields": ("rating_summary",)}),
        ("Analitika", {"classes": ("collapse",), "fields": ("created_by", "views_count", "reads_count", "downloads_count", "created_at", "updated_at")} ),
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(admin_avg_rating=Avg("reviews__rating", filter=models_q("reviews__is_approved", True)), admin_review_count=Count("reviews", filter=models_q("reviews__is_approved", True)))

    @admin.display(description="Banner")
    def banner_preview(self, obj):
        if obj.banner:
            return format_html('<img class="kx-banner-thumb" src="{}" alt="{}">', obj.banner.url, obj.title)
        return format_html('<span class="kx-thumb-empty">BN</span>')

    @admin.display(description="Kitob", ordering="title")
    def title_block(self, obj):
        category = obj.category.name if obj.category else "Kategoriyasiz"
        return format_html(
            '<strong class="kx-strong">{}</strong><small class="kx-subtitle">{}</small>',
            obj.title,
            category,
        )

    @admin.display(description="Banner ko'rinishi")
    def banner_large_preview(self, obj):
        if obj and obj.banner:
            return format_html('<img src="{}" alt="{}" class="kx-banner-large">', obj.banner.url, obj.title)
        return "Banner yuklanmagan"

    @admin.display(description="Muqova ko'rinishi")
    def cover_large_preview(self, obj):
        if obj and obj.cover:
            return format_html('<img src="{}" alt="{}" class="kx-cover-large">', obj.cover.url, obj.title)
        return "Muqova yuklanmagan"

    @admin.display(description="PDF link")
    def pdf_link(self, obj):
        if obj and obj.pdf_file:
            return format_html('<a class="kx-admin-link" href="{}" target="_blank">PDF faylni ko\'rish</a>', obj.pdf_file.url)
        return "PDF yuklanmagan"

    @admin.display(description="Baho")
    def rating_summary(self, obj):
        if not obj or not obj.pk:
            return "Kitob saqlangandan keyin baholar ko'rinadi."
        avg = obj.average_rating
        count = obj.review_count
        return format_html('<div class="kx-rating-summary"><strong>{}/5</strong><span>{} ta izoh</span></div>', avg, count)

    @admin.display(description="Kategoriya", ordering="category__name")
    def category_badge(self, obj):
        if obj.category:
            return format_html('<span class="kx-admin-badge">{}</span>', obj.category.name)
        return format_html('<span class="kx-admin-badge kx-muted">Kategoriyasiz</span>')

    @admin.display(description="Baho", ordering="admin_avg_rating")
    def rating_badge(self, obj):
        avg = getattr(obj, "admin_avg_rating", None) or 0
        count = getattr(obj, "admin_review_count", None) or 0
        return format_html('<span class="kx-admin-badge kx-pink">{}/5 · {}</span>', round(avg, 1), count)

    @admin.display(description="PDF", ordering="pdf_file")
    def pdf_status(self, obj):
        if obj.pdf_file:
            return format_html('<span class="kx-admin-badge kx-green">PDF bor</span>')
        return format_html('<span class="kx-admin-badge kx-rose">PDF yo\'q</span>')

    @admin.display(description="Tavsiya", ordering="is_featured")
    def featured_badge(self, obj):
        if obj.is_featured:
            return format_html('<span class="kx-admin-badge kx-pink">Tavsiya</span>')
        return format_html('<span class="kx-admin-badge kx-muted">Oddiy</span>')

    @admin.display(description="O'qish", ordering="reads_count")
    def reads_badge(self, obj):
        return format_html('<span class="kx-admin-badge">{}</span>', obj.reads_count)

    @admin.display(description="Yuklash", ordering="downloads_count")
    def downloads_badge(self, obj):
        return format_html('<span class="kx-admin-badge">{}</span>', obj.downloads_count)

    def save_model(self, request, obj, form, change):
        if not obj.created_by_id and request.user.is_authenticated:
            obj.created_by = request.user
        obj.full_clean()
        super().save_model(request, obj, form, change)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "book_count", "read_sum", "coverage_badge")
    search_fields = ("name",)
    ordering = ("name",)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(total_books=Count("books"), total_reads=Sum("books__reads_count"))

    @admin.display(description="Kitoblar soni", ordering="total_books")
    def book_count(self, obj):
        return format_html('<span class="kx-admin-badge">{}</span>', obj.total_books)

    @admin.display(description="O'qishlar", ordering="total_reads")
    def read_sum(self, obj):
        return format_html('<span class="kx-admin-badge">{}</span>', obj.total_reads or 0)

    @admin.display(description="Holat")
    def coverage_badge(self, obj):
        if obj.total_books:
            return format_html('<span class="kx-admin-badge kx-green">Faol bo\'lim</span>')
        return format_html('<span class="kx-admin-badge kx-muted">Bo\'sh bo\'lim</span>')


@admin.action(description="Tanlangan izohlarni ko'rinadigan qilish")
def approve_reviews(modeladmin, request, queryset):
    queryset.update(is_approved=True)


@admin.action(description="Tanlangan izohlarni yashirish")
def hide_reviews(modeladmin, request, queryset):
    queryset.update(is_approved=False)


@admin.register(BookReview)
class BookReviewAdmin(admin.ModelAdmin):
    list_display = ("book_title", "user_display_admin", "rating_badge", "comment_preview", "approved_badge", "updated_at")
    list_filter = ("rating", "is_approved", "created_at", "updated_at")
    search_fields = ("book__title", "book__author", "user__username", "user__email", "comment")
    autocomplete_fields = ("book", "user")
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("book", "user")
    date_hierarchy = "created_at"
    ordering = ("-updated_at",)
    actions = (approve_reviews, hide_reviews)

    @admin.display(description="Kitob", ordering="book__title")
    def book_title(self, obj):
        return obj.book.title

    @admin.display(description="Foydalanuvchi", ordering="user__username")
    def user_display_admin(self, obj):
        return obj.user_display

    @admin.display(description="Baho", ordering="rating")
    def rating_badge(self, obj):
        return format_html('<span class="kx-admin-badge kx-pink">{}/5</span>', obj.rating)

    @admin.display(description="Izoh")
    def comment_preview(self, obj):
        text = obj.comment[:80] + ("…" if len(obj.comment) > 80 else "")
        return text

    @admin.display(description="Holat", ordering="is_approved")
    def approved_badge(self, obj):
        if obj.is_approved:
            return format_html('<span class="kx-admin-badge kx-green">Ko\'rinadi</span>')
        return format_html('<span class="kx-admin-badge kx-muted">Yashirilgan</span>')


# Django importini yuqorida qat'iy ushlab turish uchun kichik yordamchi.
def models_q(field, value):
    from django.db.models import Q

    return Q(**{field: value})
