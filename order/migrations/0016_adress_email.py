# Generated by Django 5.0.13 on 2025-03-28 07:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0015_adress_first_name_adress_last_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='adress',
            name='email',
            field=models.EmailField(blank=True, max_length=254, verbose_name='E-Posta'),
        ),
    ]
