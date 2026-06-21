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
]
