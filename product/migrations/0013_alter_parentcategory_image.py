# Generated by Django 4.2.17 on 2025-02-11 15:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0012_remove_category_image_parentcategory_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='parentcategory',
            name='image',
            field=models.ImageField(blank=True, upload_to='parentCategory', verbose_name='Resim'),
        ),
    ]
