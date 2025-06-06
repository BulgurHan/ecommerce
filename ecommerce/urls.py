from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from page.views import home ,allProdCat, ProdCatDetail, product_search, tracking_order, send_verification_code,confirm_cancelation
from product.views import add_cart, cart_detail, update_cart,PaymentPage, save_address

admin.site.site_header = "NoTag Yönetim Paneli"
admin.site.site_title = "NoTag Admin"
admin.site.index_title = "Yönetim Paneline Hoş Geldiniz"


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('api/', include(('page.urls', 'page'), namespace='page')), 
    path('kategori/<slug:parent_slug>/', allProdCat, name='parent_category'),
    path('kategori/<slug:parent_slug>/<slug:category_slug>/', allProdCat, name='sub_category'),
    path('<slug:c_slug>/<slug:product_slug>/', ProdCatDetail , name='ProdCatDetail'),
    path('add_cart/', add_cart, name='add_cart'),
    path('sepet/', cart_detail, name='cart_detail'),
    path('update_cart/', update_cart, name='update_cart'),
    path('payment/', PaymentPage.as_view(), name='payment'),
    path('save-address/', save_address, name='save_address'),
    path('ara/', product_search, name='product_search'),
    path('siparis-takip/', tracking_order, name='tracking_order'),
    path('send_verification_code/', send_verification_code, name='send_verification_code'),
    path('confirm-cancelation/', confirm_cancelation, name='confirm_cancelation'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
