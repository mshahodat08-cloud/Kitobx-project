from django.urls import path

from . import views

urlpatterns = [
    path("", views.book_list, name="book_list"),
    path("books/new/", views.book_create, name="book_create"),
    path("books/<int:pk>/", views.book_detail, name="book_detail"),
    path("books/<int:pk>/read/", views.book_read, name="book_read"),
    path("books/<int:pk>/pdf/", views.book_pdf_inline, name="book_pdf_inline"),
    path("books/<int:pk>/download/", views.book_download, name="book_download"),
    path("books/<int:pk>/edit/", views.book_update, name="book_update"),
    path("books/<int:pk>/delete/", views.book_delete, name="book_delete"),
    path("clubs/", views.club_list, name="club_list"),
    path("clubs/create/", views.create_club, name="create_club"),
    path("clubs/<int:pk>/", views.club_detail, name="club_detail"),
    path("clubs/<int:pk>/join/", views.join_club, name="join_club"),
    path("clubs/<int:pk>/leave/", views.leave_club, name="leave_club"),
    path("clubs/<int:pk>/message/", views.send_message, name="send_message"),

    # ── Club admin ─────────────────────────────────────
    path("clubs/<int:pk>/rules/add/", views.add_rule, name="add_rule"),
    path("clubs/<int:pk>/rules/<int:rule_pk>/delete/", views.delete_rule, name="delete_rule"),
    path("clubs/<int:pk>/plan/add/", views.add_reading_plan, name="add_reading_plan"),
    path("clubs/<int:pk>/promote/<int:user_pk>/", views.promote_to_admin, name="promote_to_admin"),]
