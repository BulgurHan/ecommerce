# Generated by Django 4.2.17 on 2025-02-09 17:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0008_alter_category_slug'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='image',
            field=models.ImageField(blank=True, upload_to='product', verbose_name='Resim'),
        ),
    ]
