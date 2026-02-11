from django.shortcuts import render, get_object_or_404
from .models import Category, Product
from cart.forms import CartAddProductForm
from .recommender import Recommender
from .models import Product 

def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)
    if category_slug:
        category = get_object_or_404(Category, 
                                     translations__slug=category_slug,
                                     translations__language_code=request.LANGUAGE_CODE)
        products = products.filter(category=category)
    return render(request,
                 'shop/product/list.html',
                 {'category': category,
                  'categories': categories,
                  'products': products})
 
def product_detail(request, id, slug):
    product = get_object_or_404(Product,
                               translations__slug=slug,  # ¡Usa translations__slug en lugar de slug!
                               translations__language_code=request.LANGUAGE_CODE, 
                               available=True)
    cart_product_form = CartAddProductForm()
    r = Recommender()
    recommended_products = r.suggest_products_for([product], 4)
    return render(request,
                 'shop/product/detail.html',
                 {'product': product,
                  'cart_product_form': cart_product_form,
                  'recommended_products': recommended_products})