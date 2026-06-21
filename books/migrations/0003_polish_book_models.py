# Manual migration prepared while cleaning the project.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("books", "0002_book_views_count"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="book",
            options={
                "ordering": ["-created_at"],
                "verbose_name": "Kitob",
                "verbose_name_plural": "Kitoblar",
            },
        ),
        migrations.AlterModelOptions(
            name="category",
            options={
                "ordering": ["name"],
                "verbose_name": "Kategoriya",
                "verbose_name_plural": "Kategoriyalar",
            },
        ),
        migrations.AlterField(
            model_name="book",
            name="category",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="books",
                to="books.category",
                verbose_name="Kategoriya",
            ),
        ),
        migrations.AlterField(
            model_name="book",
            name="cover",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to="books/",
                verbose_name="Muqova rasmi",
            ),
        ),
        migrations.AlterField(
            model_name="book",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, verbose_name="Qo'shilgan vaqt"),
        ),
        migrations.AlterField(
            model_name="book",
            name="description",
            field=models.TextField(blank=True, verbose_name="Tavsif"),
        ),
        migrations.AlterField(
            model_name="book",
            name="author",
            field=models.CharField(max_length=150, verbose_name="Muallif"),
        ),
        migrations.AlterField(
            model_name="book",
            name="published_year",
            field=models.PositiveIntegerField(verbose_name="Chop etilgan yil"),
        ),
        migrations.AlterField(
            model_name="book",
            name="title",
            field=models.CharField(max_length=255, verbose_name="Kitob nomi"),
        ),
        migrations.AlterField(
            model_name="book",
            name="views_count",
            field=models.PositiveIntegerField(default=0, verbose_name="Ko'rishlar soni"),
        ),
        migrations.AlterField(
            model_name="category",
            name="name",
            field=models.CharField(max_length=100, unique=True, verbose_name="Kategoriya nomi"),
        ),
    ]
