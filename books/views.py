from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Avg, Count, F, Q, Sum
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.text import slugify

from .forms import BookForm, BookReviewForm
from .models import Book, BookReview, Category


def is_content_admin(user):
    return user.is_authenticated and user.is_staff


def user_has_vip(user):
    if not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser:
        return True
    profile = getattr(user, "profile", None)
    return bool(profile and profile.is_vip_active)


def _book_queryset():
    return (
        Book.objects.select_related("category", "created_by")
        .annotate(
            avg_rating=Avg("reviews__rating", filter=Q(reviews__is_approved=True)),
            reviews_total=Count("reviews", filter=Q(reviews__is_approved=True)),
        )
    )


def book_list(request):
    books = _book_queryset()
    categories = Category.objects.all()

    query = request.GET.get("q", "").strip()
    author_query = request.GET.get("author", "").strip()
    category_query = request.GET.get("category", "").strip()

    if query:
        books = books.filter(
            Q(title__icontains=query)
            | Q(author__icontains=query)
            | Q(description__icontains=query)
        )
    if author_query:
        books = books.filter(author__icontains=author_query)
    if category_query:
        books = books.filter(category_id=category_query)

    featured_books = _book_queryset().filter(is_featured=True)[:6]
    filtered_count = books.count()
    total_views = Book.objects.aggregate(total=Sum("views_count"))["total"] or 0
    total_reads = Book.objects.aggregate(total=Sum("reads_count"))["total"] or 0

    context = {
        "books": books,
        "featured_books": featured_books,
        "categories": categories,
        "query": query,
        "author_query": author_query,
        "category_query": category_query,
        "total_books": Book.objects.count(),
        "total_categories": categories.count(),
        "total_views": total_views,
        "total_reads": total_reads,
        "filtered_count": filtered_count,
    }
    return render(request, "books/book_list.html", context)


@user_passes_test(is_content_admin, login_url="login")
def book_create(request):
    form = BookForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        book = form.save(commit=False)
        book.created_by = request.user
        book.save()
        form.save_m2m()
        messages.success(request, "Kitob qo'shildi. Banner va PDF majburiy fayllari tekshirildi.")
        return redirect(book.get_absolute_url())
    return render(request, "books/book_form.html", {"form": form, "page_title": "Yangi kitob qo'shish"})


@user_passes_test(is_content_admin, login_url="login")
def book_update(request, pk):
    book = get_object_or_404(Book, pk=pk)
    form = BookForm(request.POST or None, request.FILES or None, instance=book)
    if request.method == "POST" and form.is_valid():
        book = form.save()
        messages.success(request, "Kitob ma'lumotlari yangilandi.")
        return redirect(book.get_absolute_url())
    return render(
        request,
        "books/book_form.html",
        {"form": form, "book": book, "page_title": "Kitobni tahrirlash"},
    )


@user_passes_test(is_content_admin, login_url="login")
def book_delete(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == "POST":
        book.delete()
        messages.success(request, "Kitob o'chirildi.")
        return redirect("book_list")
    return render(request, "books/book_confirm_delete.html", {"book": book})


def book_detail(request, pk):
    Book.objects.filter(pk=pk).update(views_count=F("views_count") + 1)
    book = get_object_or_404(_book_queryset(), pk=pk)
    approved_reviews = (
        book.reviews.filter(is_approved=True)
        .select_related("user", "user__profile")
        .order_by("-updated_at")
    )
    rating_summary = approved_reviews.aggregate(avg=Avg("rating"), count=Count("id"))
    user_review = None

    if request.user.is_authenticated:
        user_review = BookReview.objects.filter(book=book, user=request.user).first()

    review_form = BookReviewForm(instance=user_review)
    if request.method == "POST" and request.POST.get("form_type") == "review":
        if not request.user.is_authenticated:
            messages.warning(request, "Baho va izoh yozish uchun hisobga kiring.")
            return redirect(f"{reverse('login')}?next={book.get_absolute_url()}#reviews")
        review_form = BookReviewForm(request.POST, instance=user_review)
        if review_form.is_valid():
            review = review_form.save(commit=False)
            review.book = book
            review.user = request.user
            review.is_approved = True
            review.save()
            messages.success(request, "Baho va izoh saqlandi.")
            return redirect(f"{book.get_absolute_url()}#reviews")

    context = {
        "book": book,
        "can_download": user_has_vip(request.user),
        "reviews": approved_reviews,
        "review_form": review_form,
        "user_review": user_review,
        "average_rating": round(rating_summary["avg"] or 0, 1),
        "reviews_count": rating_summary["count"] or 0,
    }
    return render(request, "books/book_detail.html", context)


@login_required
def book_read(request, pk):
    book = get_object_or_404(Book.objects.select_related("category"), pk=pk)
    if not book.pdf_file:
        messages.warning(request, "Bu kitob uchun hali PDF fayl yuklanmagan.")
        return redirect(book.get_absolute_url())
    Book.objects.filter(pk=book.pk).update(reads_count=F("reads_count") + 1)

    from premium.models import ReadingProgress

    progress, _ = ReadingProgress.objects.get_or_create(user=request.user, book=book)

    context = {
        "book": book,
        "can_download": user_has_vip(request.user),
        "progress": progress,
    }
    return render(request, "books/book_reader.html", context)


@login_required
def book_pdf_inline(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if not book.pdf_file:
        raise Http404("PDF fayl topilmadi")
    response = FileResponse(book.pdf_file.open("rb"), content_type="application/pdf")
    filename = Path(book.pdf_file.name).name
    response["Content-Disposition"] = f'inline; filename="{filename}"'
    response["X-Frame-Options"] = "SAMEORIGIN"
    return response


@login_required
def book_download(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if not book.pdf_file:
        messages.warning(request, "Bu kitob uchun PDF fayl yuklanmagan.")
        return redirect(book.get_absolute_url())
    if not user_has_vip(request.user):
        messages.warning(request, "PDF faylni yuklab olish uchun VIP obuna kerak.")
        return redirect(book.get_absolute_url())
    Book.objects.filter(pk=book.pk).update(downloads_count=F("downloads_count") + 1)
    title = slugify(book.title) or "kitob"
    filename = f"{title}.pdf"
    return FileResponse(book.pdf_file.open("rb"), as_attachment=True, filename=filename, content_type="application/pdf")
