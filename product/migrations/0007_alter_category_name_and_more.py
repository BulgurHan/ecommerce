# Generated by Django 4.2.17 on 2025-02-09 17:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0006_remove_category_parent_categories_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='name',
            field=models.CharField(max_length=250, verbose_name='İsim'),
        ),
        migrations.RemoveField(
            model_name='category',
            name='parent_categories',
        ),
        migrations.AddField(
            model_name='category',
            name='parent_categories',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='categories', to='product.parentcategory', verbose_name='Üst Kategoriler'),
        ),
    ]
