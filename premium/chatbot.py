"""🤖 AI Chatbot — KitobX platformasi bo'yicha mahalliy yordamchi.

Chatbot foydalanuvchi xabarini tahlil qilib, kitoblar bazasidan qidiruv,
AI tavsiyalar va platforma bo'yicha tez-tez beriladigan savollarga javob
beradi. Hech qanday tashqi API kalitiga muhtoj emas — barcha javoblar
loyihaning o'z ma'lumotlar bazasi asosida shakllantiriladi.
"""
import re

from django.db.models import Avg, Count, Q

from books.models import Book, Category

from .recommend import get_recommendations

GREETINGS = ("salom", "assalomu", "hi", "hello", "hey", "qalaysiz", "yaxshimisiz")
THANKS = ("rahmat", "tashakkur", "thanks", "raxmat")
BYE = ("xayr", "bye", "salomat bo'ling", "ko'rishguncha")


def _serialize(books):
    data = []
    for book in books:
        data.append({
            "id": book.id,
            "title": book.title,
            "author": book.author,
            "url": book.get_absolute_url(),
            "image": book.card_image.url if book.card_image else "",
            "rating": round(getattr(book, "avg_rating", None) or book.average_rating or 0, 1),
        })
    return data


def _book_search(text, limit=5):
    return (
        Book.objects.select_related("category")
        .annotate(avg_rating=Avg("reviews__rating", filter=Q(reviews__is_approved=True)))
        .filter(Q(title__icontains=text) | Q(author__icontains=text) | Q(description__icontains=text))
        .distinct()[:limit]
    )


def generate_reply(user, message):
    text = message.lower().strip()
    text = re.sub(r"\s+", " ", text)

    if any(word in text for word in GREETINGS):
        name = getattr(getattr(user, "profile", None), "name", None) if user else None
        hello = f"Salom, {name}! 👋" if name else "Salom!"
        return {
            "reply": f"{hello} Men KitobX AI yordamchisiman. Kitob qidirishda, tavsiya tanlashda yoki VIP "
                     f"obuna bo'yicha savollaringizga javob bera olaman. Nimadan boshlaymiz?",
            "books": [],
        }

    if any(word in text for word in THANKS):
        return {"reply": "Marhamat! Yana savolingiz bo'lsa, bemalol yozavering. 📚", "books": []}

    if any(word in text for word in BYE):
        return {"reply": "Xayr! Yaxshi o'qishlar tilayman. 👋", "books": []}

    if "vip" in text or "obuna" in text or "yuklab ol" in text or "pdf yukla" in text:
        return {
            "reply": (
                "VIP obuna sizga barcha kitoblarni PDF formatda cheklovsiz yuklab olish imkonini beradi. "
                "Rejalarni \"VIP\" sahifasida ko'rishingiz va bir necha soniyada faollashtirishingiz mumkin."
            ),
            "books": [],
            "action": {"label": "VIP rejalarni ko'rish", "url": "/vip/"},
        }

    if any(word in text for word in ("tavsiya", "nima o'qisam", "qaysi kitob", "maslahat", "taklif")):
        recs = get_recommendations(user, limit=4)
        if recs:
            return {
                "reply": "Sizning didingiz asosida quyidagi kitoblarni tavsiya qilaman:",
                "books": _serialize(recs),
            }
        return {"reply": "Hozircha tavsiya uchun yetarli ma'lumot yo'q, lekin katalogni ko'rib chiqishingiz mumkin.", "books": []}

    if any(word in text for word in ("challenge", "marafon", "maqsad", "yillik reja")):
        return {
            "reply": (
                "Reading Challenge orqali yiliga necha ta kitob o'qishni rejalashtirishingiz va "
                "progressingizni kuzatishingiz mumkin. \"Challenge\" sahifasida maqsad belgilang!"
            ),
            "books": [],
            "action": {"label": "Challenge sahifasi", "url": "/challenge/"},
        }

    if any(word in text for word in ("necha", "qancha kitob", "statistika")):
        total = Book.objects.count()
        cats = Category.objects.count()
        return {
            "reply": f"Hozirda platformada {total} ta kitob va {cats} ta kategoriya mavjud.",
            "books": [],
        }

    category_match = Category.objects.filter(name__icontains=text.split()[-1] if text else "")
    if not category_match.exists():
        for word in text.split():
            if len(word) > 3:
                category_match = Category.objects.filter(name__icontains=word)
                if category_match.exists():
                    break

    if category_match.exists():
        books = (
            Book.objects.filter(category__in=category_match)
            .annotate(avg_rating=Avg("reviews__rating", filter=Q(reviews__is_approved=True)))
            .order_by("-avg_rating", "-views_count")[:4]
        )
        if books:
            cat_name = category_match.first().name
            return {
                "reply": f"\"{cat_name}\" kategoriyasidan eng yaxshi kitoblar:",
                "books": _serialize(books),
            }

    found = _book_search(text)
    if found:
        plural = "ta kitob" if len(found) != 1 else "ta kitob"
        return {
            "reply": f"\"{message.strip()}\" bo'yicha {len(found)} {plural} topildi:",
            "books": _serialize(found),
        }

    return {
        "reply": (
            "Kechirasiz, aniq tushunmadim 🤔. Kitob nomi, muallif yoki janr nomini yozib ko'ring — "
            "masalan: \"tarix kitoblari\" yoki \"menga kitob tavsiya qil\". Shuningdek VIP yoki "
            "Reading Challenge haqida ham so'rashingiz mumkin."
        ),
        "books": [],
    }
