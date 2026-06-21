from django.contrib import admin
from django.utils.html import format_html

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


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ("user", "book", "created_at")
    search_fields = ("user__username", "book__title")
    list_select_related = ("user", "book")
    date_hierarchy = "created_at"


@admin.register(ReadingProgress)
class ReadingProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "book", "progress_badge", "is_completed", "updated_at")
    list_filter = ("is_completed",)
    search_fields = ("user__username", "book__title")
    list_select_related = ("user", "book")

    @admin.display(description="Progress")
    def progress_badge(self, obj):
        color = "#059669" if obj.percent >= 100 else "#d41473"
        return format_html('<strong style="color:{}">{}</strong>%', color, obj.percent)


@admin.register(ReadingHistory)
class ReadingHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "book", "action", "percent_at_event", "created_at")
    list_filter = ("action", "created_at")
    search_fields = ("user__username", "book__title")
    list_select_related = ("user", "book")
    date_hierarchy = "created_at"


@admin.register(ReadingChallenge)
class ReadingChallengeAdmin(admin.ModelAdmin):
    list_display = ("user", "year", "goal", "completed_count", "progress_percent")
    list_filter = ("year",)
    search_fields = ("user__username",)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "title", "icon", "is_read", "created_at")
    list_filter = ("icon", "is_read")
    search_fields = ("user__username", "title", "message")
    date_hierarchy = "created_at"


@admin.register(VIPPlan)
class VIPPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "duration_days", "is_popular", "sort_order")
    list_editable = ("is_popular", "sort_order")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(VIPTransaction)
class VIPTransactionAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "amount", "status", "created_at")
    list_filter = ("status", "plan")
    search_fields = ("user__username",)
    date_hierarchy = "created_at"


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "content_preview", "created_at")
    list_filter = ("role",)
    search_fields = ("user__username", "content")
    date_hierarchy = "created_at"

    @admin.display(description="Matn")
    def content_preview(self, obj):
        return obj.content[:80] + ("…" if len(obj.content) > 80 else "")
