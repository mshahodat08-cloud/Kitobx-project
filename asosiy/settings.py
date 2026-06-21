"""
Django settings for kutubxona_project.

Loyiha SQLite bilan ishlaydi. Hostingga chiqarishda kerakli qiymatlarni
muhit o'zgaruvchilari orqali berish mumkin:
- DJANGO_SECRET_KEY
- DJANGO_DEBUG=0
- DJANGO_ALLOWED_HOSTS=example.com,www.example.com
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-kutubxona-local-dev-key-change-on-production",
)

DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"

_default_hosts = "127.0.0.1,localhost"
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", _default_hosts).split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts.apps.AccountsConfig",
    "books",
    "premium",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "asosiy.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "premium.context_processors.premium_context",
            ],
        },
    },
]

WSGI_APPLICATION = "asosiy.wsgi.application"

# Har qanday hostingda ham SQLite ishlashi uchun yagona sozlama.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "uz"
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "book_list"
LOGOUT_REDIRECT_URL = "book_list"

# Admin panel uchun qo'shimcha himoya. Productionda env orqali almashtiring.
ADMIN_ACCESS_CODE = os.getenv("ADMIN_ACCESS_CODE", "2026")
ADMIN_LOCKOUT_ATTEMPTS = int(os.getenv("ADMIN_LOCKOUT_ATTEMPTS", "5"))
ADMIN_LOCKOUT_SECONDS = int(os.getenv("ADMIN_LOCKOUT_SECONDS", "600"))
