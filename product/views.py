from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.template.loader import get_template
from product.models import Product,ProductVariant
from order.models import Order, OrderItem, Cart, CartItem, Adress
import iyzipay
import json
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt

# Cart için session id üreten yardımcı fonksiyon
def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart



# Sepete ürün ekleme
def add_cart(request):
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            product_id = data.get('product_id')
            size = data.get('size')
            quantity = int(data.get('quantity', 1))

            print(f"Product ID: {product_id}, Size: {size}, Quantity: {quantity}")  # Debug

            # Ürünü bul
            product = get_object_or_404(Product, id=product_id)
            print(f"Product found: {product.name}")  # Debug

            # Varyantı bul
            variant = get_object_or_404(ProductVariant, product=product, size=size)
            print(f"Variant found: {variant.size}")  # Debug

            # Sepeti bul veya oluştur
            if request.user.is_authenticated:
                cart, created = Cart.objects.get_or_create(user=request.user)
            else:
                session_key = request.session.session_key
                if not session_key:
                    request.session.create()
                    session_key = request.session.session_key
                cart, created = Cart.objects.get_or_create(cart_id=session_key)

            # Sepet öğesini bul veya oluştur
            cart_item, created = CartItem.objects.get_or_create(
                product=product,
                variant=variant,  # Variant alanı kullanılıyor
                cart=cart,
                user=request.user if request.user.is_authenticated else None
            )

            if not created:
                if cart_item.quantity + quantity <= variant.stock:
                    cart_item.quantity += quantity
                else:
                    return JsonResponse({'success': False, 'message': 'Yeterli stok yok.'})
            else:
                cart_item.quantity = quantity

            cart_item.save()
            cart.update_total()  # Sepetin toplam tutarını güncelle
            return JsonResponse({'success': True, 'message': 'Ürün sepete eklendi.'})
        except Exception as e:
            print(f"Hata: {e}")  # Hata mesajını yazdır
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Geçersiz istek.'})



# Sepet detayları 
def cart_detail(request, total=0, counter=0):
    # Adres bilgisi var mi kontrol et
    try:
        adres = Adress.objects.get(user=request.user)
    except ObjectDoesNotExist:
        adres = None

    # Sepet bilgilerini al
    cart = None
    cart_items = []

    if request.user.is_authenticated:
        # Kullanıcı giriş yapmışsa, kullanıcıya ait sepeti getir
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        # Kullanıcı giriş yapmamışsa, session_key ile sepeti ilişkilendir
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(cart_id=session_key)

    # Sepet öğelerini getir
    if cart:
        cart_items = CartItem.objects.filter(cart=cart, active=True)

    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'adres' : adres
    })


@csrf_exempt
def update_cart(request):
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            cart_item_id = data.get('cart_item_id')
            quantity = data.get('quantity')

            if cart_item_id is None or quantity is None:
                return JsonResponse({'success': False, 'message': 'Eksik veri gönderildi.'})

            quantity = int(quantity)  # Eğer burası hata verirse, 'except ValueError' çalışır.

            print(f"Cart Item ID: {cart_item_id}, Quantity: {quantity}")  # Debug

            # Sepet öğesini bul
            cart_item = CartItem.objects.get(id=cart_item_id)

            if quantity > 0:
                # Miktarı güncelle
                cart_item.quantity = quantity
                cart_item.save()
            else:
                # Miktar 0 veya daha küçük ise sepet öğesini sil
                cart_item.delete()

            # Sepetin toplam tutarını güncelle
            cart_item.cart.update_total()

            return JsonResponse({
                'success': True,
                'message': 'Sepet güncellendi.'
            })
        except CartItem.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Sepet öğesi bulunamadı.'})
        except ValueError:
            return JsonResponse({'success': False, 'message': 'Geçersiz miktar.'})
        except Exception as e:
            print(f"Hata: {e}")  # Debug
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Geçersiz istek.'})


def payment(request):
    return render(request, 'payment.html',{})



# Sipariş detaylarını e-posta ile gönderme
def sendEmail(order_id):
    transaction = Order.objects.get(id=order_id)
    order_items = OrderItem.objects.filter(order=transaction)
    try:
        subject = "noTAG - Yeni Sipariş #{}".format(transaction)
        to = ['{}'.format(transaction.emailAddress)]
        from_email = "hurkus.siparis@gmail.com"
        order_information = {
            'transaction': transaction,
            'order_items': order_items
        }
        message = get_template('email/email.html').render(order_information)
        msg = EmailMessage(subject, message, to=to, from_email=from_email)
        msg.content_subtype = 'html'
        msg.send()
    except IOError as e:
        return e






# Iyzico API anahtarları ve URL
API_KEY = settings.IYZICO_API_KEY
SECRET_KEY = settings.IYZICO_SECRET_KEY
BASE_URL = "sandbox-api.iyzipay.com"
PAYMENT_OPTIONS = {
    "api_key": API_KEY,
    "secret_key": SECRET_KEY,
    "base_url": BASE_URL,
}


class PaymentPage(TemplateView):
    template_name = 'payment.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        buyer = {
            'id': 'BY789',
            'name': 'John',
            'surname': 'Doe',
            'gsmNumber': '+905350000000',
            'email': 'email@email.com',
            'identityNumber': '74300864791',
            'lastLoginDate': '2015-10-05 12:43:35',
            'registrationDate': '2013-04-21 15:12:09',
            'registrationAddress': 'Nidakule Göztepe, Merdivenköy Mah. Bora Sok. No:1',
            'ip': '85.34.78.112',
            'city': 'Istanbul',
            'country': 'Turkey',
            'zipCode': '34732'
        }

        address = {
            'contactName': 'Jane Doe',
            'city': 'Istanbul',
            'country': 'Turkey',
            'address': 'Nidakule Göztepe, Merdivenköy Mah. Bora Sok. No:1',
            'zipCode': '34732'
        }

        basket_items = [
            {
                'id': 'BI101',
                'name': 'Binocular',
                'category1': 'Collectibles',
                'category2': 'Accessories',
                'itemType': 'PHYSICAL',
                'price': '0.3'
            },
            {
                'id': 'BI102',
                'name': 'Game code',
                'category1': 'Game',
                'category2': 'Online Game Items',
                'itemType': 'VIRTUAL',
                'price': '0.5'
            },
            {
                'id': 'BI103',
                'name': 'Usb',
                'category1': 'Electronics',
                'category2': 'Usb / Cable',
                'itemType': 'PHYSICAL',
                'price': '0.2'
            }
        ]

        request = {
            'locale': 'tr',
            'conversationId': '123456789',
            'price': '1',
            'paidPrice': '1.2',
            'currency': 'TRY',
            'basketId': 'B67832',
            'paymentGroup': 'PRODUCT',
            "callbackUrl": "http://localhost:8000/api/result",
            "enabledInstallments": ['2', '3', '6', '9'],
            'buyer': buyer,
            'shippingAddress': address,
            'billingAddress': address,
            'basketItems': basket_items,
        }

        checkout_form_initialize = iyzipay.CheckoutFormInitialize().create(request, PAYMENT_OPTIONS)
        content = json.loads(checkout_form_initialize.read().decode('utf-8'))
        context['form'] = content.get("checkoutFormContent", "")
        return context


class CheckoutView(TemplateView):
    template_name = 'checkout.html'


class PaymentStatusView(TemplateView):
    template_name = 'status.html'

    def get(self, request, *args, **kwargs):
        status = request.GET.get('status', None)

        if status == 'success':
            messages.add_message(request, messages.SUCCESS, "payment successful.")
        elif status == 'fail':
            messages.add_message(request, messages.ERROR, "payment could not be received")
        else:
            messages.add_message(request, messages.ERROR, "unknown error while receiving payment")

        return super().get(request, *args, **kwargs)


@csrf_exempt
def payment_result(request):
    if request.method == "POST":
        try:
            raw_data = json.loads(request.body)
            conversation_id = raw_data.get("conversationId")
            status = raw_data.get("status")

            if status == "SUCCESS":
                return JsonResponse({"message": "Ödeme başarılı!", "conversation_id": conversation_id})
            else:
                return JsonResponse({"message": "Ödeme başarısız!", "error": raw_data}, status=400)

        except Exception as e:
            return JsonResponse({"error": "Bir hata oluştu.", "details": str(e)}, status=500)

    return JsonResponse({"error": "Bu endpoint yalnızca POST isteklerini kabul eder."}, status=405)


def save_address(request):
    if request.method == 'POST':
        # Formdan gelen verileri al
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone = request.POST.get('phone')
        city = request.POST.get('city')
        district = request.POST.get('district')
        post_code = request.POST.get('post_code')
        address = request.POST.get('address')

        # kullanici giriş yapmış ise Adress objesi olustur ve kaydet
        if request.user.is_authenticated:
            adres, created = Adress.objects.update_or_create(
                            user=request.user,  
                            defaults={  
                                'phone': phone,
                                'city': city,
                                'district': district,
                                'postCode': post_code,
                                'address': address,
                                }
                            )
            
        # kullanici giris yapmamis ise Adresi session'a kaydet
        request.session['shipping_address'] = {
            'first_name': first_name,
            'last_name': last_name,
            'phone': phone,
            'city': city,
            'district': district,
            'post_code': post_code,
            'address': address,
        }

        return redirect('payment')  # Payment sayfasına yönlendir
    else:
        messages.error(request, 'Geçersiz istek.')
        return redirect('cart') # Sepet sayfasına yönlendir
