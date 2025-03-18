from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from page.views import home ,allProdCat, ProdCatDetail
from product.views import add_cart, cart_detail, update_cart,PaymentPage,CheckoutView,PaymentStatusView, save_address



urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('kategori/<slug:parent_slug>/', allProdCat, name='parent_category'),
    path('kategori/<slug:parent_slug>/<slug:category_slug>/', allProdCat, name='sub_category'),
    path('<slug:c_slug>/<slug:product_slug>/', ProdCatDetail , name='ProdCatDetail'),
    path('add_cart/', add_cart, name='add_cart'),
    path('sepet/', cart_detail, name='cart_detail'),
    path('update_cart/', update_cart, name='update_cart'),
    path('payment/', PaymentPage.as_view(), name='payment'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('status/', PaymentStatusView.as_view(), name='payment_status'),
    path('save-address/', save_address, name='save_address'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
