from datetime import date

from django import forms

from .models import Book, BookReview


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = [
            "title",
            "author",
            "published_year",
            "category",
            "description",
            "cover",
            "banner",
            "pdf_file",
            "is_featured",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Masalan: Yashamoq"}),
            "author": forms.TextInput(attrs={"placeholder": "Masalan: Yu Hua"}),
            "published_year": forms.NumberInput(attrs={"placeholder": "Masalan: 2024", "min": 1}),
            "description": forms.Textarea(attrs={"rows": 5, "placeholder": "Kitob haqida qisqacha yozing..."}),
            "cover": forms.FileInput(attrs={"accept": "image/png,image/jpeg,image/webp"}),
            "banner": forms.FileInput(attrs={"accept": "image/png,image/jpeg,image/webp"}),
            "pdf_file": forms.FileInput(attrs={"accept": "application/pdf"}),
        }
        labels = {
            "banner": "Banner rasmi (majburiy)",
            "pdf_file": "PDF kitob (majburiy)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = (field.widget.attrs.get("class", "") + " form-input").strip()
        self.fields["banner"].required = True
        self.fields["pdf_file"].required = True

    def clean_published_year(self):
        year = self.cleaned_data["published_year"]
        max_year = date.today().year + 1
        if year < 1 or year > max_year:
            raise forms.ValidationError(f"Yil 1 dan {max_year} gacha bo'lishi kerak.")
        return year

    def clean_banner(self):
        banner = self.cleaned_data.get("banner") or getattr(self.instance, "banner", None)
        if not banner:
            raise forms.ValidationError("Kitob saqlanishi uchun banner rasmi yuklash majburiy.")
        return banner

    def clean_pdf_file(self):
        pdf_file = self.cleaned_data.get("pdf_file") or getattr(self.instance, "pdf_file", None)
        if not pdf_file:
            raise forms.ValidationError("PDF fayl majburiy. PDF yuklanmasa kitob umuman saqlanmaydi.")
        return pdf_file


class BookReviewForm(forms.ModelForm):
    rating = forms.TypedChoiceField(
        label="Baho",
        coerce=int,
        choices=BookReview.RATING_CHOICES,
        widget=forms.RadioSelect(attrs={"class": "rating-radio"}),
    )

    class Meta:
        model = BookReview
        fields = ["rating", "comment"]
        labels = {"comment": "Izoh"}
        widgets = {
            "comment": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Kitob haqida fikringizni yozing...",
                    "class": "form-input",
                }
            )
        }

    def clean_rating(self):
        rating = self.cleaned_data["rating"]
        if rating < 1 or rating > 5:
            raise forms.ValidationError("Baho 1 dan 5 gacha bo'lishi kerak.")
        return rating

    def clean_comment(self):
        comment = (self.cleaned_data.get("comment") or "").strip()
        if len(comment) < 3:
            raise forms.ValidationError("Izoh kamida 3 ta belgidan iborat bo'lishi kerak.")
        return comment
