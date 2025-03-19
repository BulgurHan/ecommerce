from django.shortcuts import render,get_object_or_404
from rest_framework.views import APIView
from django.core.paginator import Paginator, EmptyPage
from django.shortcuts import reverse, resolve_url
from rest_framework.response import Response
from django.http import HttpResponseRedirect
from django.contrib import messages
import json
import random
import pprint
import iyzipay
from ecommerce.settings import PAYMENT_OPTIONS
from product.models import Collection, ParentCategory, Category, Product
from order.models import PaymentModel, Cart, CartItem, Adress




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


def get_basket_items(cart):
    basket_items = []
    
    for item in cart.cartitem_set.all():
        basket_items.append({
            'id': f"BI0{item.id}",  # ID formatı için BI ekledik
            'name': item.product.name,
            'category1': item.product.category.name if item.product.category else "General",
            'category2': item.variant.name if item.variant else "Default",
            'itemType': "PHYSICAL" if item.product.is_physical else "VIRTUAL",
            'price': str(item.product.price)  # Decimal alanı stringe çevrildi
        })
    
    return basket_items


class Payment(APIView):
    def get(self, request, *args, **kwargs):
        # request_host = request.get_host()
        # path = reverse('api:payment:result')
        # callback_url = f'{request_host}{path}'
        callback_url = f"{request.scheme}://{request.get_host()}{reverse('sepet')}"
        payment_model: PaymentModel = PaymentModel.objects.create()
        cart = Cart.objects.get(user=request.user)
        basket_items = get_basket_items(cart)
        adres = Adress.objects.get(user = request.user)
        buyer = {
            'id': str(request.user.pk),
            'name': str(request.user.first_name),
            'surname': str(request.user.last_name),
            'gsmNumber': f'+9{adres.phone}' if adres.phone else '',
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

        request = {
            'locale': 'tr',
            'conversationId': payment_model.conversationId,
            'price': cart.total,
            'paidPrice': cart.total,
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

        # print(checkout_form_initialize.read().decode('utf-8'))
        page = checkout_form_initialize
        header = {'Content-Type': 'application/json'}
        content = checkout_form_initialize.read().decode('utf-8')
        json_content = json.loads(content)
        print(json_content)
        pprint.pprint(json_content)
        payment_model.token = json_content["token"]
        payment_model.save()
        print(type(json_content))
        print(json_content["checkoutFormContent"])
        print("************************")
        print(json_content["token"])
        print("************************")
        form = json_content["checkoutFormContent"]
        # form.replace('<script>', '')
        # form.replace('</script>', '')
        return Response({'message': 'ok :)', 'context': json_content["checkoutFormContent"]}, status=201)
    




class ResultView(APIView):
    def post(self, request, *args, **kwargs):
        if token := request.data.get('token', None):
            payment_model: PaymentModel = get_object_or_404(PaymentModel, token=token)
            request = {
                'locale': payment_model.locale,
                'conversationId': payment_model.conversationId,
                'token': token
            }
            checkout_form_result = iyzipay.CheckoutForm().retrieve(request, PAYMENT_OPTIONS)
            print("************************")
            print(type(checkout_form_result))
            result = checkout_form_result.read().decode('utf-8')
            print(result)
            pyload = json.loads(result)
            '''
            paymentStatus : could be SUCCESS, FAILURE, INIT_THREEDS, CALLBACK_THREEDS, BKM_POS_SELECTED, CALLBACK_PECCO
            '''
            pprint.pprint(pyload)

            if payment_status := pyload.get('paymentStatus', None):
                result_path = reverse('cart_detail')
                match payment_status:
                    case 'SUCCESS':
                        payment_model.status = "success"
                        payment_model.save()
                        # messages.success(request,"Ödeme başarıyla alındı.")
                        return HttpResponseRedirect(result_path)
                    case _:
                        return HttpResponseRedirect(f'{result_path}?status=fail')
                    