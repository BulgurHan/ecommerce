from django.shortcuts import render, redirect, get_object_or_404
from django.shortcuts import reverse, resolve_url
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.template.loader import get_template
from product.models import Product,ProductVariant
from order.models import Order, OrderItem, Cart, CartItem, Adress, PaymentModel
import iyzipay
import json
from datetime import datetime
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from ecommerce.settings import PAYMENT_OPTIONS



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



def cart_detail(request, total=0, counter=0):
    # Adres bilgisi var mı kontrol et
    try:
        if request.user.is_authenticated:
            adres = Adress.objects.get(user=request.user)
        else:
            adres = Adress.objects.get(address_id = request.session.session_key)
    except:
        adres = None

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
        
        # user=None olarak belirtiyoruz, çünkü anonim kullanıcıya user atanamaz
        cart, created = Cart.objects.get_or_create(cart_id=session_key, defaults={"user": None})

    # Sepet öğelerini getir
    if cart:
        cart_items = CartItem.objects.filter(cart=cart, active=True)

    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'adres': adres
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







def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')


def get_basket_items(cart):
    basket_items = []
    
    for item in cart.cartitem_set.all():
        basket_items.append({
            'id': f"BI0{item.id}",  # ID formatı için BI ekledik
            'name': item.product.name,
            'category1': "General",
            'category2': "Giyim",
            'itemType': "PHYSICAL",
            'price': str(item.product.price * item.quantity)  # Toplam fiyat
        })
    
    return basket_items

class PaymentPage(TemplateView):
    template_name = 'payment.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request
        callback_url = f"{request.scheme}://{request.get_host()}{reverse('page:result')}"            
        if request.user.is_authenticated:
            payment_model: PaymentModel = PaymentModel.objects.create(user=request.user)   
            cart = Cart.objects.get(user=request.user)
            adres = Adress.objects.get(user = request.user)
            buyer = {
            'id': str(request.user.pk),
            'name': str(request.user.first_name),
            'surname': str(request.user.last_name),
            'gsmNumber': f'+90{adres.phone}' if adres.phone else '',
            'email': str(request.user.email),
            'identityNumber': '22222222222',
            'lastLoginDate': str(request.user.last_login),
            'registrationDate': str(request.user.date_joined),
            'registrationAddress': str(adres.address),
            'ip': get_client_ip(request),
            'city': str(adres.city),
            'country': 'Turkey',
            'zipCode': str(adres.postCode)
        }

            address = {
                'contactName': f'{request.user.first_name} {request.user.last_name}',
                'city': str(adres.city),
                'country': 'Turkey',
                'address': str(adres.address),
                'zipCode': str(adres.postCode)
            }
        else:
            adres = Adress.objects.get(address_id = request.session.session_key)
            payment_model: PaymentModel = PaymentModel.objects.create(payment_id = request.session.session_key)   
            cart = Cart.objects.get(cart_id = request.session.session_key)
            buyer = {
            'id': str(adres.pk),
            'name': str(adres.first_name),
            'surname': str(adres.last_name),
            'gsmNumber': f'+90{adres.phone}' if adres.phone else '',
            'email': str(adres.email),
            'identityNumber': '22222222222',
            'lastLoginDate': str(datetime.now()),
            'registrationDate': str(datetime.now()),
            'registrationAddress': str(adres.address),
            'ip': get_client_ip(request),
            'city': str(adres.city),
            'country': 'Turkey',
            'zipCode': str(adres.postCode)
            }

            address = {
                'contactName': f'{adres.first_name} {adres.last_name}',
                'city': str(adres.city),
                'country': 'Turkey',
                'address': str(adres.address),
                'zipCode': str(adres.postCode)
            }
        basket_items = get_basket_items(cart)
        


        request = {
            'locale': 'tr',
            'conversationId': payment_model.conversationId,
            'price': str(cart.total),
            'paidPrice': str(cart.total),
            'currency': 'TRY',
            'basketId': str(cart.pk),
            'paymentGroup': 'PRODUCT',
            "callbackUrl": callback_url,
            "enabledInstallments": ['2', '3', '6', '9'],
            'buyer': buyer,
            'shippingAddress': address,
            'billingAddress': address,
            'basketItems': basket_items,
            # 'debitCardAllowed': True
        }
        checkout_form_initialize = iyzipay.CheckoutFormInitialize().create(request, PAYMENT_OPTIONS)
        content = json.loads(checkout_form_initialize.read().decode('utf-8'))  # Zaten JSON formatında bir Python dict olacak
        context['form'] = content.get("checkoutFormContent", "")  # Güvenli erişim için .get() kullanıyoruz
        token = content.get("token")  # JSON'dan token alınıyor
        payment_model.token = token  # Token modelde saklanıyor
        payment_model.save()

        return context



class CheckoutView(TemplateView):
    template_name = 'checkout.html'







def save_address(request):
    if request.method == 'POST':
        # Formdan gelen verileri al
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
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
                                'first_name': first_name,
                                'last_name': last_name,
                                'email': email,  
                                'phone': phone,
                                'city': city,
                                'district': district,
                                'postCode': post_code,
                                'address': address,
                                }
                            )
            
        # kullanici giris yapmamis ise Adresi session'a kaydet
        adres, created = Adress.objects.update_or_create(
                address_id=request.session.session_key,  
                defaults={
                    "first_name" : first_name,
                    "last_name" : last_name,
                    'email': email,  
                    'phone': phone,
                    'city': city,
                    'district': district,
                    'postCode': post_code,
                    'address': address,
                    }
                )

        return redirect('payment')  # Payment sayfasına yönlendir
    else:
        messages.error(request, 'Geçersiz istek.')
        return redirect('cart') # Sepet sayfasına yönlendir
