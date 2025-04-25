from django.shortcuts import render,get_object_or_404
from rest_framework.views import APIView
from django.core.paginator import Paginator, EmptyPage
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
import json
import random
import iyzipay
from ecommerce.settings import PAYMENT_OPTIONS
from product.models import Collection, ParentCategory, Category, Product
from order.models import PaymentModel, Cart, CartItem, Adress, Order, OrderItem
from order.models import sendEmail
from django.http import JsonResponse
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.crypto import get_random_string


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
        'products': products,
        'title' : f'{parent_category} - {category.name}' if category else 'Tüm Ürünler',
    })



def ProdCatDetail(request, c_slug, product_slug):
    product = get_object_or_404(Product, category__slug=c_slug, slug=product_slug)
    return render(request, 'product.html', {
        'title': product.name,
        'product': product,
        'latest_products': Product.objects.filter(avaible=True).only('id', 'name', 'price', 'imageOne').order_by('-created')[:10],  
        }
        )


def product_search(request):
    query = request.GET.get('q')
    if query:
        products = Product.objects.filter(name__icontains=query)
    else:
        products = Product.objects.all()
    return render(request, 'category.html', {'products': products, 'query': query, 'search': True})


def tracking_order(request):
    if request.method == 'POST':
        tracking_number = request.POST.get('tracking_number')
        try:
            order = Order.objects.get(tracking_number=tracking_number)
            return render(request, 'order_tracking.html', {'order': order,'title': 'Sipariş Takip'})
        except Order.DoesNotExist:
            messages.error(request, "Bu takip numarasına ait sipariş bulunamadı.")
            return render(request, 'order_tracking.html', {'title': 'Sipariş Takip'})
    else:
        return render(request, 'order_tracking.html', {'title': 'Sipariş Takip'})

@csrf_exempt  # eğer JavaScript üzerinden POST atılacaksa gerekli olabilir
def send_verification_code(request):
    if request.method == "POST":
        order_id = request.POST.get("order_id")

        try:
            order = get_object_or_404(Order, id=order_id)
            code = get_random_string(length=6, allowed_chars='0123456789')

            # kodu session'a kaydet
            request.session['cancel_code'] = code
            request.session['cancel_order_id'] = order_id

            send_mail(
                subject="Sipariş İptal Doğrulama Kodu",
                message=f"Siparişinizi iptal etmek için bu kodu girin: {code}",
                from_email="destek@notagfashion.com",
                recipient_list=[order.emailAddress],
                fail_silently=False,
            )
            order.cancel_code = code
            order.cancel_code_created = timezone.now()
            order.save()

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


@require_POST
def confirm_cancelation(request):
    order_id = request.POST.get('order_id')
    entered_code = request.POST.get('verification_code')

    if not order_id or not entered_code:
        return JsonResponse({'success': False, 'message': 'Tüm alanlar zorunludur.'}, status=400)

    try:
        order = get_object_or_404(Order, id=int(order_id))
    except ValueError:
        return JsonResponse({'success': False, 'message': 'Geçersiz sipariş ID.'}, status=400)

    if order.cancel_code != entered_code:
        return JsonResponse({'success': False, 'message': 'Doğrulama kodu hatalı.'}, status=403)

    # Mail gönder
    sendEmail(
        order_id=order.id,
        status="cancelled",
    )

    # Stok geri ekle


    order.status = 'Iptal Edildi'
    order.cancel_confirmed = True
    order.save()

    return JsonResponse({'success': True, 'message': 'Siparişiniz iptal edildi.'})
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

                # Sipariş e-postası gönder
                sendEmail(order_id=order.id,status="created")

                messages.success(request, "Ödeme başarıyla tamamlandı.")
                return HttpResponseRedirect(result_path)

            else:
                messages.warning(request, "Ödeme alınamadı.")
                return HttpResponseRedirect(result_path)

                    