from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class ParentCategory(models.Model):
    name = models.CharField(
        max_length=250,
        unique=True,
        verbose_name='Üst Kategori İsmi'
    )
    slug = models.SlugField(
        max_length=250,
        unique=True,
        verbose_name='Slug - Lütfen Burayı Değiştirmeyin-',
        blank=True
    )
    image = models.ImageField(
        upload_to = 'parentCategory',
        blank = True,
        verbose_name = 'Resim'
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Üst Kategori'
        verbose_name_plural = 'Üst Kategoriler'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)  # İsme göre slug oluştur
        super().save(*args, **kwargs)
    def get_url(self):
        return reverse('parent_category', args=[self.slug])
    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(
        max_length=250,
        verbose_name='İsim'
    )
    slug = models.SlugField(
        max_length=250,
        verbose_name='Slug - Lütfen Burayı Değiştirmeyin-',
        blank=True  # Otomatik olarak oluşturulacak
    )
    parent_categories = models.ForeignKey(
        ParentCategory,
        related_name='categories',  # Üst kategoriler üzerinden erişim için
        verbose_name='Üst Kategoriler',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Kategori'
        verbose_name_plural = 'Kategoriler'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)  # İsme göre slug oluştur
        super().save(*args, **kwargs)

    def __str__(self):
        return '{}-{}'.format(self.parent_categories,self.name )


class Collection(models.Model):
    name = models.CharField(
        max_length=250,
        unique=True,
        verbose_name='İsim'
    )
    slug = models.SlugField(
        max_length=250,
        unique=True,
        verbose_name='Slug - Lütfen Burayı Değiştirmeyin-',
        blank=True  # Otomatik olarak oluşturulacak
    )
    description = models.TextField(
        blank=True,
        verbose_name='Açıklama'
    )
    image = models.ImageField(
        upload_to = 'collection',
        blank = True,
        verbose_name = 'Resim'
    )
    class Meta:
        ordering = ('name',)
        verbose_name = 'Koleksiyon'
        verbose_name_plural = 'Koleksiyonlar'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)  # İsme göre slug oluştur
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        max_length=250,
        unique=True,
        verbose_name='İsim'
    )
    slug = models.SlugField(
        max_length=250,
        unique=True,
        verbose_name='Slug - Lütfen Burayı Değiştirmeyin-',
        blank=True  # Otomatik olarak oluşturulacak
    )
    description = models.TextField(
        blank=True,
        verbose_name='Açıklama'
    )
    collection = models.ForeignKey(
        'Collection',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='collections',
        verbose_name='Koleksiyon'
    )
    category = models.ForeignKey(
        'Category',
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name='Kategori'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Tutar'
    )
    imageOne = models.ImageField(
        upload_to='product',
        blank=True,
        verbose_name='Resim 1'
    )
    imageTwo = models.ImageField(
        upload_to='product',
        null=True,
        blank=True,
        verbose_name='Resim 2'
    )
    imageThree = models.ImageField(
        upload_to='product',
        blank=True,
        null=True,
        verbose_name='Resim 3'
    )
    avaible = models.BooleanField(
        default=True,
        verbose_name='Yayınlandı'
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Oluşturulma Tarihi'
    )
    updated = models.DateTimeField(
        auto_now=True,
        verbose_name='Güncellenme Tarihi'
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ürün'
        verbose_name_plural = 'Ürünler'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)  # İsme göre slug oluştur
        super().save(*args, **kwargs)

    def get_url(self):
        return reverse('ProdCatDetail', args=[self.category.slug, self.slug])

    def total_stock(self):
        return sum(variant.stock for variant in self.variants.all())

    def __str__(self):
        return self.name



class ProductVariant(models.Model):
    SIZE_CHOICES = [
        ('S', 'Small'),
        ('M', 'Medium'),
        ('L', 'Large'),
        ('XL', 'X-Large'),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants',
        verbose_name='Ürün'
    )
    size = models.CharField(
        max_length=2,
        choices=SIZE_CHOICES,
        verbose_name='Beden'
    )
    stock = models.PositiveIntegerField(
        verbose_name='Stok'
    )

    class Meta:
        unique_together = ('product', 'size')  # Aynı ürün için aynı beden birden fazla eklenemez

    def __str__(self):
        return f"{self.product.name} - {self.get_size_display()}"
