from django.db import models
from django.db.models import Sum
from django.utils.crypto import get_random_string
import random
from django.template.loader import get_template
from django.db.models.signals import post_save
from product.models import Product,ProductVariant
from accounts.models import CustomUser
from django.core.mail import EmailMessage
from django.template.loader import get_template



# Siparişle ilgili e-posta gönderme fonksiyonu
def sendEmail(order_id, status="created"):
    transaction = Order.objects.get(id=order_id)
    order_items = OrderItem.objects.filter(order=transaction)

    subject_map = {
        "created": f"noTAG - Yeni Sipariş #{transaction.tracking_number}",
        "shipped": f"noTAG - Siparişiniz Kargoya Verildi #{transaction.tracking_number}",
        "cancelled": f"noTAG - Siparişiniz İptal Edildi #{transaction.tracking_number}",
    }

    template_map = {
        "created": "email/order_created.html",
        "shipped": "email/order_shipped.html",
        "cancelled": "email/order_cancelled.html",
    }

    try:
        subject = subject_map.get(status, f"noTAG - Sipariş Durumu #{transaction.tracking_number}")
        to = [transaction.emailAddress]  
        from_email = "destek@notagfashion.com"

        context = {
            'transaction': transaction,
            'order_items': order_items,
        }

        template_path = template_map.get(status, "email/order_created.html")
        message = get_template(template_path).render(context)

        msg = EmailMessage(subject, message, to=to, from_email=from_email)
        msg.content_subtype = 'html'
        msg.send()

    except Exception as e:
        print("Mail gönderim hatası:", e)
        return e



STATUS_CHOICES = [
    ('Hazırlanıyor', 'Hazırlanıyor'),
    ('Kargoda', 'Kargoda'),
    ('Teslim Edildi', 'Teslim Edildi'),
    ('Iptal Edildi', 'İptal Edildi'),
]

    

class Order(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    token = models.CharField(max_length=250, blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='TL Sipariş Toplamı')
    emailAddress = models.EmailField(max_length=250, blank=True, verbose_name='E-mail')
    created = models.DateField(auto_now_add=True, verbose_name='Tarih')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Telefon')
    billingName = models.CharField(max_length=250, blank=True, verbose_name='Alıcı Adı')
    billingAddress1 = models.CharField(max_length=250, blank=True, verbose_name='Alıcı Adresi')
    billingCity = models.CharField(max_length=250, blank=True, verbose_name='Alıcının Şehri')
    billingDistrict = models.CharField(max_length=250, blank=True, verbose_name='Alıcının İlçesi')
    billingPostCode = models.CharField(max_length=10, blank=True, verbose_name='Alıcı Posta Kodu')
    shippingName = models.CharField(max_length=250, blank=True, verbose_name='Alıcı Adı')
    shippingAddress1 = models.CharField(max_length=250, blank=True, verbose_name='Kargo Adresi')
    shippingCity = models.CharField(max_length=250, blank=True, verbose_name='Kargo Şehri')
    shippingDistrict = models.CharField(max_length=250, blank=True, verbose_name='Kargo İlçesi')
    shippingPostCode = models.CharField(max_length=10, blank=True, verbose_name='Kargo Posta Kodu')
    status = models.CharField(max_length=15, default='Hazırlanıyor', choices=STATUS_CHOICES, verbose_name="Durum")
    kargo = models.IntegerField(default=0, verbose_name="Kargo Takip Numarası")
    tracking_number = models.CharField(max_length=6, blank=True, null=True, verbose_name="Sipariş Takip Numarası")
    cancel_code = models.CharField(max_length=6, blank=True, null=True)
    cancel_code_created = models.DateTimeField(blank=True, null=True) 
    cancel_confirmed = models.BooleanField(default=False)

    class Meta:
        db_table = 'order'
        ordering = ('-created',)
        verbose_name = 'Sipariş'
        verbose_name_plural = 'Siparişler'

    def save(self, *args, **kwargs):
        if not self.tracking_number:
            self.tracking_number = self.generate_tracking_number()
        super().save(*args, **kwargs)

    def generate_tracking_number(self):
        while True:
            number = str(random.randint(100000, 999999))  # 6 haneli sayı üret
            if not Order.objects.filter(tracking_number=number).exists():
                return number

    def calculate_total(self):
        """
        Siparişin toplam tutarını hesaplar.
        """
        total = sum(item.sub_total() for item in self.items.all())  
        return total


    def __str__(self):
        return str(self.id)


    
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Ürün")
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Varyant")
    quantity = models.PositiveIntegerField(verbose_name="Adet")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Fiyat")

    class Meta:
        db_table = 'OrderItem'

    def sub_total(self):
        return self.quantity * self.price
    def __str__(self):
        return f"{self.product.name} - {self.product_variant.get_size_display() if self.product_variant else 'Bilinmeyen Varyant'}"



def order_post_save(sender, instance, **kwargs):
    if instance.status == 'Kargoda':
        sendEmail(order_id=instance.id, status="shipped")
post_save.connect(order_post_save, sender=Order)




class Cart(models.Model):
    cart_id = models.CharField(max_length=250, blank=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    date_added = models.DateField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = 'Cart'
        ordering = ['date_added']

    def update_total(self):
        # Sepet öğelerinin toplam tutarını hesapla ve total alanına kaydet
        self.total = sum(item.sub_total() for item in self.cartitem_set.all())
        self.save()
        
    def __str__(self):
        return f"{self.user}"


class CartItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True)  
    quantity = models.IntegerField(default=1)
    active = models.BooleanField(default=True)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        db_table = 'CartItem'

    def sub_total(self):
        return self.product.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
    


class Adress(models.Model):
    address_id = models.CharField(max_length=250, blank=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=50, blank=True, verbose_name="İsim")
    last_name = models.CharField(max_length=50, blank=True, verbose_name="Soyisim")
    email = models.EmailField(max_length=254, blank=True, verbose_name="E-Posta")
    phone = models.CharField(max_length=20, blank=True, verbose_name='Telefon')
    address = models.CharField(max_length=250, blank=True, verbose_name='Alıcı Adresi')
    city = models.CharField(max_length=250, blank=True, verbose_name='Alıcının İli')
    district = models.CharField(max_length=250, blank=True, verbose_name='Alıcının İlçesi')
    postCode = models.CharField(max_length=10, blank=True, verbose_name='Alıcı Posta Kodu')



class PaymentModel(models.Model):
    STATUS_CHOICES = [
        ('success', 'Başarılı'),
        ('failure', 'Başarısız'),
        ('pending', 'Beklemede'),
    ]
    payment_id = models.CharField(max_length=250, blank=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    locale = models.CharField(max_length=10, default='tr')
    conversationId = models.CharField(max_length=10, blank=True)
    token = models.CharField(max_length=50, default=None, blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending') 
    
    @staticmethod
    def generate_random_id(length=10):
        return ''.join(str(random.randint(0, 9)) for _ in range(length))

    def save(self, *args, **kwargs):
        if not self.pk and not self.conversationId:
            self.conversationId = self.generate_random_id()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.locale} - {self.conversationId} - {self.get_status_display()}'