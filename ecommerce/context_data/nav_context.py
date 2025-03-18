from django.shortcuts import get_object_or_404
from order.models import Cart, CartItem
from product.models import ParentCategory, Category



def menu_links(request):
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

    # Context'i oluştur
    return {
        'parent_categories': ParentCategory.objects.only('id', 'name'),
        'categories': Category.objects.only('id', 'name', 'parent_categories'),
        'cart': cart,
        'cart_items': cart_items,
    }