from django.shortcuts import render,get_object_or_404
from rest_framework.views import APIView
from django.core.paginator import Paginator, EmptyPage
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from rest_framework.response import Response
from django.http import HttpResponseRedirect
from django.contrib import messages
import json
import random
import pprint
import iyzipay
from ecommerce.settings import PAYMENT_OPTIONS
from product.models import Collection, ParentCategory, Category, Product
from order.models import PaymentModel, Cart, CartItem, Adress, Order, OrderItem




def home(request):
    # Kullanılabilir ürünlerin ID'lerini al
    product_ids = list(Product.objects.filter(avaible=True).values_list('id', flat=True))
    
    # Rastgele 10 ürün seç (ürün sayısı 10'dan azsa mevcut olanları getir)
    random_ids = random.sample(product_ids, min(len(product_ids), 10)) if product_ids else []
    
    # Kategorilere göre ürünleri gruplama
    categorized_products = {}
    for category in Category.objects.only('id', 'name', 'parent_categories'):
        categorized_products[category.name] = Product.objects.filter(category=category, avaible=True).only('id', 'name', 'price', 'imageOne')[:10]
    
    context = {
        'collections': Collection.objects.only('id', 'name'),  # Sadece gerekli alanları çekerek optimizasyon
        'latest_products': Product.objects.filter(avaible=True).only('id', 'name', 'price', 'imageOne').order_by('-created')[:10],  
        'categorized_products': categorized_products  # Her kategori için ürünleri içeren dict
    }

    return render(request, 'home.html', context)





def allProdCat(request, parent_slug=None, category_slug=None):
    parent_category = None
    category = None

    if parent_slug:
        # Üst kategoriyi al, ebeveyni olmayan bir kategori olmalı
        parent_category = get_object_or_404(ParentCategory, slug=parent_slug)

        if category_slug:
            # Alt kategoriyi al, ebeveyni üst kategori olmalı
            category = get_object_or_404(Category, slug=category_slug, parent_categories=parent_category)
            products_list = Product.objects.filter(category=category, avaible=True)
        else:
            # Sadece üst kategori seçildiyse, alt kategorilerdeki ürünleri getir
            products_list = Product.objects.filter(category__parent_categories=parent_category, avaible=True)
    else:
        # Hiç kategori seçilmezse tüm ürünleri getir
        products_list = Product.objects.filter(avaible=True)

    # Sayfalama (Pagination)
    paginator = Paginator(products_list, 8)
    page_number = request.GET.get('page', 1)

    try:
        products = paginator.page(page_number)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    return render(request, 'category.html', {
        'parent_category': parent_category,
        'category': category,
        'products': products
    })



def ProdCatDetail(request, c_slug, product_slug):
    product = get_object_or_404(Product, category__slug=c_slug, slug=product_slug)
    return render(request, 'product.html', {
        'product': product,
        'latest_products': Product.objects.filter(avaible=True).only('id', 'name', 'price', 'imageOne').order_by('-created')[:10],  
        }
        )




#---------------------------------------İYZİCO-------------------------------------------

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')




    



class ResultView(APIView):
    def post(self, request, *args, **kwargs):
        token = request.data.get('token', None)
        if token:
            payment_model: PaymentModel = get_object_or_404(PaymentModel, token=token)
            request_data = {
                'locale': payment_model.locale,
                'conversationId': payment_model.conversationId,
                'token': token
            }
            checkout_form_result = iyzipay.CheckoutForm().retrieve(request_data, PAYMENT_OPTIONS)
            result = checkout_form_result.read().decode('utf-8')
            pyload = json.loads(result)

            payment_status = pyload.get('paymentStatus', None)
            result_path = reverse('cart_detail')

            if payment_status == 'SUCCESS':
                payment_model.status = "success"
                payment_model.save()
                user = payment_model.user
                session_key = payment_model.payment_id
                if request.user.is_authenticated:
                    adres = Adress.objects.get(user=user)
                    cart = Cart.objects.get(user=user)
                else:
                    adres = Adress.objects.get(address_id = session_key)
                    cart = Cart.objects.get(cart_id = session_key)
                    user = None

                order = Order.objects.create(
                    user=user,
                    token=payment_model.token,
                    total=0,  # İlk başta 0 olarak oluştur
                    emailAddress=adres.email,
                    phone=adres.phone,
                    billingName=f'{adres.first_name} {adres.last_name}',
                    billingAddress1=adres.address,
                    billingCity=adres.city,
                    billingPostCode=adres.postCode,
                    billingDistrict=adres.district,
                    shippingName=f'{adres.first_name} {adres.last_name}',
                    shippingAddress1=adres.address,
                    shippingCity=adres.city,
                    shippingPostCode=adres.postCode,
                    shippingDistrict=adres.district,
                )

                
                for item in CartItem.objects.filter(cart=cart):
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        price=item.product.price,
                        quantity=item.quantity,
                         product_variant = item.variant
                    )

                # Toplam fiyatı hesapla ve güncelle
                order.total = order.calculate_total()
                order.save()

                # Sepeti temizle
                cart.delete()

                messages.success(request, "Ödeme başarıyla tamamlandı.")
                return HttpResponseRedirect(result_path)

            else:
                messages.warning(request, "Ödeme alınamadı.")
                return HttpResponseRedirect(result_path)

                    