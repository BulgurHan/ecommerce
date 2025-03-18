from django.shortcuts import render,get_object_or_404
from django.core.paginator import Paginator, EmptyPage
import random
from product.models import Collection, ParentCategory, Category, Product




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

