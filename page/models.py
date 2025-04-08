from django.db import models
from django.core.exceptions import ValidationError



class Email(models.Model):
    email = models.EmailField(unique=True)

    def clean(self):
        if Email.objects.exists() and not self.pk:
            raise ValidationError("Sadece bir tane e-posta adresi kaydedilebilir.")

    def save(self, *args, **kwargs):
        self.full_clean() 
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email
    
    class Meta:
        verbose_name = "Email"
        verbose_name_plural = "Email"


class Phone(models.Model):
    phone = models.CharField(max_length=20, unique=True)
    def clean(self):
        if Phone.objects.exists() and not self.pk:
            raise ValidationError("Sadece bir tane telefon numarası kaydedilebilir.")

    def save(self, *args, **kwargs):
        self.full_clean() 
        super().save(*args, **kwargs)

    def __str__(self):
        return self.phone
    
    class Meta:
        verbose_name = "Telefon"
        verbose_name_plural = "Telefon"



class Kargo(models.Model):
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Tutar'
    )

    def clean(self):
        if Kargo.objects.exists() and not self.pk:
            raise ValidationError("Sadece bir tane kargo fiyatı tanımlanabilir.")

    def save(self, *args, **kwargs):
        self.full_clean() 
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.price} TL"
    
    class Meta:
        verbose_name = "Kargo Fiyatlandırması"
        verbose_name_plural = "Kargo Fiyatlandırması"

