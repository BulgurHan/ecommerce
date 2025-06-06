# Generated by Django 4.2.17 on 2025-04-25 07:17

from django.db import migrations, models
import product.models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0014_remove_product_image_remove_product_stock_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='parentcategory',
            name='image',
            field=models.ImageField(blank=True, upload_to=product.models.turkish_file_rename, verbose_name='Resim'),
        ),
        migrations.AlterField(
            model_name='product',
            name='imageOne',
            field=models.ImageField(blank=True, upload_to=product.models.turkish_file_rename, verbose_name='Resim 1'),
        ),
        migrations.AlterField(
            model_name='product',
            name='imageThree',
            field=models.ImageField(blank=True, null=True, upload_to=product.models.turkish_file_rename, verbose_name='Resim 3'),
        ),
        migrations.AlterField(
            model_name='product',
            name='imageTwo',
            field=models.ImageField(blank=True, null=True, upload_to=product.models.turkish_file_rename, verbose_name='Resim 2'),
        ),
    ]
