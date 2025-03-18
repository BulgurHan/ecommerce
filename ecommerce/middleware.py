from django.utils.deprecation import MiddlewareMixin
from order.models import Cart, CartItem

class MergeCartMiddleware(MiddlewareMixin):
    def _cart_id(self, request):
        cart = request.session.session_key
        if not cart:
            cart = request.session.create()
        return cart

    def process_request(self, request):
        if request.user.is_authenticated:
            session_key = self._cart_id(request)  # self._cart_id kullanıldı
            if session_key:
                # Kullanıcıya ait olmayan sepet öğelerini bul
                anonymous_cart = Cart.objects.filter(cart_id=session_key, user__isnull=True).first()
                if anonymous_cart:
                    # Sepet öğelerini kullanıcıya ata
                    CartItem.objects.filter(cart=anonymous_cart).update(user=request.user)
                    anonymous_cart.delete()