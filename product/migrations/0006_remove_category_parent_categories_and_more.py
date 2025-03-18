# Generated by Django 4.2.17 on 2025-02-09 17:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0005_remove_category_parent_categories_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='category',
            name='parent_categories',
        ),
        migrations.AddField(
            model_name='category',
            name='parent_categories',
            field=models.ManyToManyField(related_name='categories', to='product.parentcategory', verbose_name='Üst Kategoriler'),
        ),
    ]
