from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin.forms import AdminAuthenticationForm
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.db.models import Count
from django.shortcuts import redirect, get_object_or_404
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html

from .models import Profile


User = get_user_model()


def _client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


class SecureAdminAuthenticationForm(AdminAuthenticationForm):
    admin_code = forms.CharField(
        label="Admin access code",
        widget=forms.PasswordInput(attrs={"autocomplete": "one-time-code", "placeholder": "Qo'shimcha admin kod"}),
    )
    website = forms.CharField(required=False, widget=forms.HiddenInput)

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-input")
        self.fields["username"].widget.attrs.setdefault("placeholder", "Admin username")
        self.fields["password"].widget.attrs.setdefault("placeholder", "Admin parol")

    def _rate_key(self):
        if not self.request:
            return "admin-login:unknown"
        return f"admin-login:{_client_ip(self.request)}"

    def _increase_failures(self):
        key = self._rate_key()
        attempts = cache.get(key, 0) + 1
        cache.set(key, attempts, getattr(settings, "ADMIN_LOCKOUT_SECONDS", 600))
        return attempts

    def clean(self):
        key = self._rate_key()
        max_attempts = getattr(settings, "ADMIN_LOCKOUT_ATTEMPTS", 5)
        if cache.get(key, 0) >= max_attempts:
            raise forms.ValidationError("Juda ko'p urinish bo'ldi. Bir necha daqiqadan keyin qayta urinib ko'ring.")

        code = self.cleaned_data.get("admin_code")
        honeypot = self.cleaned_data.get("website")
        expected = getattr(settings, "ADMIN_ACCESS_CODE", "2026")
        if honeypot or code != expected:
            self._increase_failures()
            raise forms.ValidationError("Admin access code noto'g'ri.")

        try:
            cleaned = super().clean()
        except forms.ValidationError:
            self._increase_failures()
            raise

        cache.delete(key)
        return cleaned


admin.site.login_form = SecureAdminAuthenticationForm
admin.site.login_template = "admin/login.html"


try:
    admin.site.unregister(User)
except NotRegistered:
    pass

try:
    admin.site.unregister(Group)
except NotRegistered:
    pass


@admin.action(description="Tanlangan userlarga VIP berish")
def grant_vip(modeladmin, request, queryset):
    count = 0
    for user in queryset:
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.is_vip = True
        profile.vip_expires_at = None
        profile.save(update_fields=["is_vip", "vip_expires_at", "updated_at"])
        count += 1
    messages.success(request, f"{count} ta foydalanuvchiga VIP berildi.")


@admin.action(description="Tanlangan userlardan VIPni olib tashlash")
def revoke_vip(modeladmin, request, queryset):
    count = Profile.objects.filter(user__in=queryset).update(is_vip=False, vip_expires_at=None, updated_at=timezone.now())
    messages.success(request, f"{count} ta profildan VIP olib tashlandi.")


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """User ma'lumotlari bu panelda tahrirlanmaydi.

    Admin uchun faqat VIP berish/olish, aktiv holatni ko'rish va userni o'chirish
    kerak. Shu sabab change form readonly, ro'yxatda esa alohida VIP tugmasi bor.
    """

    list_display = (
        "user_identity",
        "email_display",
        "phone_display",
        "vip_badge",
        "active_badge",
        "vip_quick_action",
        "date_joined",
        "last_login",
    )
    list_display_links = ("user_identity",)
    list_filter = ("is_active", "is_staff", "is_superuser", "profile__is_vip", "date_joined", "last_login")
    search_fields = ("username", "first_name", "last_name", "email", "profile__display_name", "profile__phone")
    ordering = ("-date_joined",)
    date_hierarchy = "date_joined"
    list_per_page = 25
    actions = (grant_vip, revoke_vip)
    readonly_fields = (
        "readonly_identity",
        "readonly_email",
        "readonly_phone",
        "readonly_vip",
        "readonly_dates",
        "readonly_permissions",
        "readonly_instruction",
    )
    fields = readonly_fields

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        # Change page ochiladi, lekin ma'lumot saqlashga ruxsat berilmaydi.
        return request.user.is_active and request.user.is_staff

    def get_readonly_fields(self, request, obj=None):
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        return None

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("<int:user_id>/grant-vip/", self.admin_site.admin_view(self.grant_vip_view), name="auth_user_grant_vip"),
            path("<int:user_id>/revoke-vip/", self.admin_site.admin_view(self.revoke_vip_view), name="auth_user_revoke_vip"),
        ]
        return custom_urls + urls

    def grant_vip_view(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.is_vip = True
        profile.vip_expires_at = None
        profile.save(update_fields=["is_vip", "vip_expires_at", "updated_at"])
        messages.success(request, f"{user.username} uchun VIP yoqildi.")
        return redirect(request.META.get("HTTP_REFERER") or reverse("admin:auth_user_changelist"))

    def revoke_vip_view(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        Profile.objects.filter(user=user).update(is_vip=False, vip_expires_at=None, updated_at=timezone.now())
        messages.success(request, f"{user.username} uchun VIP o'chirildi.")
        return redirect(request.META.get("HTTP_REFERER") or reverse("admin:auth_user_changelist"))

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("profile").annotate(total_books=Count("books"))

    @admin.display(description="Foydalanuvchi", ordering="username")
    def user_identity(self, obj):
        profile = getattr(obj, "profile", None)
        name = (profile.display_name if profile and profile.display_name else obj.get_full_name() or obj.username)
        subtitle = f"@{obj.username}"
        if profile and profile.avatar:
            avatar_html = f'<img class="kx-user-avatar" src="{profile.avatar.url}" alt="{name}">'
        else:
            initials = (name or obj.username or "U")[:2].upper()
            avatar_html = f'<span class="kx-user-avatar">{initials}</span>'
        return format_html(
            '<span class="kx-user-cell">{}<span><strong class="kx-strong">{}</strong><small class="kx-subtitle">{}</small></span></span>',
            format_html(avatar_html),
            name,
            subtitle,
        )

    @admin.display(description="Email", ordering="email")
    def email_display(self, obj):
        return obj.email or "—"

    @admin.display(description="Telefon", ordering="profile__phone")
    def phone_display(self, obj):
        profile = getattr(obj, "profile", None)
        return profile.phone if profile and profile.phone else "—"

    @admin.display(description="VIP", ordering="profile__is_vip")
    def vip_badge(self, obj):
        profile = getattr(obj, "profile", None)
        if profile and profile.is_vip_active:
            return format_html('<span class="kx-admin-badge kx-pink">VIP</span>')
        return format_html('<span class="kx-admin-badge kx-muted">Oddiy</span>')

    @admin.display(description="Holat", ordering="is_active")
    def active_badge(self, obj):
        if obj.is_active:
            return format_html('<span class="kx-admin-badge kx-green">Aktiv</span>')
        return format_html('<span class="kx-admin-badge kx-rose">Bloklangan</span>')

    @admin.display(description="VIP qilish")
    def vip_quick_action(self, obj):
        profile = getattr(obj, "profile", None)
        if profile and profile.is_vip_active:
            url = reverse("admin:auth_user_revoke_vip", args=[obj.pk])
            return format_html('<a class="kx-mini-admin-btn kx-danger" href="{}">VIPni olish</a>', url)
        url = reverse("admin:auth_user_grant_vip", args=[obj.pk])
        return format_html('<a class="kx-mini-admin-btn" href="{}">VIP berish</a>', url)

    @admin.display(description="Profil")
    def readonly_identity(self, obj):
        return self.user_identity(obj)

    @admin.display(description="Email")
    def readonly_email(self, obj):
        return self.email_display(obj)

    @admin.display(description="Telefon")
    def readonly_phone(self, obj):
        return self.phone_display(obj)

    @admin.display(description="VIP holati")
    def readonly_vip(self, obj):
        profile = getattr(obj, "profile", None)
        if profile:
            status = profile.vip_label
        else:
            status = "Oddiy hisob"
        return format_html('<div class="kx-vip-box"><strong>{}</strong><div class="kx-vip-actions">{}</div></div>', status, self.vip_quick_action(obj))

    @admin.display(description="Vaqtlar")
    def readonly_dates(self, obj):
        return format_html(
            '<div class="kx-readonly-lines"><span>Ro\'yxatdan: {}</span><span>Oxirgi kirish: {}</span></div>',
            obj.date_joined.strftime("%d.%m.%Y %H:%M") if obj.date_joined else "—",
            obj.last_login.strftime("%d.%m.%Y %H:%M") if obj.last_login else "—",
        )

    @admin.display(description="Ruxsat")
    def readonly_permissions(self, obj):
        role = "Superadmin" if obj.is_superuser else "Staff" if obj.is_staff else "Oddiy user"
        return format_html('<span class="kx-admin-badge">{}</span>', role)

    @admin.display(description="Eslatma")
    def readonly_instruction(self, obj):
        return format_html(
            '<div class="kx-admin-note"><strong>User ma\'lumotlari tahrirlanmaydi.</strong><span>VIP berish/olish uchun yuqoridagi tugmadan yoki ro\'yxatdagi actions menyusidan foydalaning. Userni o\'chirish uchun Django adminning delete amalidan foydalaning.</span></div>'
        )
