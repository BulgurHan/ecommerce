# Generated by Django 5.0.13 on 2025-03-28 06:58

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0013_order_user'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='adress',
            name='address_id',
            field=models.CharField(blank=True, max_length=250),
        ),
        migrations.AddField(
            model_name='paymentmodel',
            name='payment_id',
            field=models.CharField(blank=True, max_length=250),
        ),
        migrations.AlterField(
            model_name='adress',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
