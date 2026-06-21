from django.urls import path

from . import views

urlpatterns = [
    path("wishlist/", views.wishlist_view, name="wishlist"),
    path("wishlist/<int:pk>/toggle/", views.wishlist_toggle, name="wishlist_toggle"),

    path("tarix/", views.reading_history_view, name="reading_history"),
    path("progress/<int:pk>/update/", views.update_progress, name="update_progress"),

    path("challenge/", views.challenge_view, name="challenge"),

    path("tavsiyalar/", views.recommendations_view, name="recommendations"),

    path("vip/", views.vip_plans_view, name="vip_plans"),
    path("vip/<slug:slug>/subscribe/", views.vip_subscribe, name="vip_subscribe"),

    path("bildirishnomalar/", views.notifications_view, name="notifications"),
    path("bildirishnomalar/<int:pk>/read/", views.notification_mark_read, name="notification_mark_read"),
    path("bildirishnomalar/read-all/", views.notifications_mark_all_read, name="notifications_mark_all_read"),

    path("chatbot/message/", views.chatbot_message, name="chatbot_message"),
]
