# Generated by Django 5.0.13 on 2025-03-28 07:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0014_adress_address_id_paymentmodel_payment_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='adress',
            name='first_name',
            field=models.CharField(blank=True, max_length=50, verbose_name='İsim'),
        ),
        migrations.AddField(
            model_name='adress',
            name='last_name',
            field=models.CharField(blank=True, max_length=50, verbose_name='Soyisim'),
        ),
    ]
