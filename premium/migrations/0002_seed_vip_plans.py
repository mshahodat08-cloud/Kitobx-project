from django.db import migrations


def seed_plans(apps, schema_editor):
    VIPPlan = apps.get_model("premium", "VIPPlan")
    plans = [
        dict(
            name="Oylik VIP",
            slug="oylik-vip",
            tagline="Bir oylik to'liq imkoniyat",
            price=29000,
            duration_days=30,
            is_popular=False,
            sort_order=1,
            features="Cheksiz PDF yuklab olish\nReklamasiz o'qish\nAI tavsiyalar\nReading Challenge",
        ),
        dict(
            name="Yillik VIP",
            slug="yillik-vip",
            tagline="Eng tejamkor reja — 2 oy bepul",
            price=249000,
            duration_days=365,
            is_popular=True,
            sort_order=2,
            features="Cheksiz PDF yuklab olish\nReklamasiz o'qish\nAI tavsiyalar\nReading Challenge\nUstuvor qo'llab-quvvatlash\nErta kirish: yangi kitoblar",
        ),
        dict(
            name="Umrbod VIP",
            slug="umrbod-vip",
            tagline="Bir martalik to'lov — cheksiz muddat",
            price=590000,
            duration_days=0,
            is_popular=False,
            sort_order=3,
            features="Cheksiz PDF yuklab olish\nReklamasiz o'qish\nAI tavsiyalar\nReading Challenge\nUstuvor qo'llab-quvvatlash\nErta kirish: yangi kitoblar\nMaxsus VIP belgisi",
        ),
    ]
    for plan in plans:
        VIPPlan.objects.update_or_create(slug=plan["slug"], defaults=plan)


def remove_plans(apps, schema_editor):
    VIPPlan = apps.get_model("premium", "VIPPlan")
    VIPPlan.objects.filter(slug__in=["oylik-vip", "yillik-vip", "umrbod-vip"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("premium", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_plans, remove_plans),
    ]
