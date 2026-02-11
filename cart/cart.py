from decimal import Decimal
from django.conf import settings 
from shop.models import Product 
from coupons.models import Coupon

class Cart(object):
    
    def __init__(self, request):
        """
        Inicializacion del carro
        """
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            #salvar un carro vacio en session 
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart
        #Almacenar el cupon aplicado 
        self.coupon_id = request.session.get('coupon_id')
    @property
    def coupon(self):
        if self.coupon_id:
                return Coupon.objects.get(id=self.coupon_id)
        return None

    def get_discount(self):
        if self.coupon:
            return (self.coupon.discount / Decimal('100')) * self.get_total_price()
        return Decimal('0')

    def get_total_price_after_discount(self):
        return self.get_total_price() - self.get_discount()
        
    def add(self, product, quantity=1, update_quantity=False):
        """
        Añadir un producto al carro o actualizar la cantidad 
        """
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id]={'quantity': 0, 
                                   'price': str(product.price)}
        if update_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity
        self.save()
    
    def save(self):
        #marcar la sesion como modificada para asegurarnos 
        #que se guarde 
        self.session.modified = True
        
    def remove(self, product):
        """
        Eliminar un producto del carro.
        """
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()
    
    def __iter__(self):
        """
        Itear sobre los elementos de carro y recuperar los 
        productos de base de datos 
        """
        product_ids = self.cart.keys()
        #Recuperar los prodcutos y añadiros al carro
        products = Product.objects.filter(id__in=product_ids)
        
        cart = self.cart.copy()
        for product in products:
            cart[str(product.id)]['product'] = product
            
        for item in cart.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item
            
    def __len__(self):
        """
        Contar todos los elementos del carro
        """
        return sum(item['quantity'] for item in self.cart.values())
            
    def get_total_price(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())
            
    def clear(self):
        #remove cart from session
        del self.session[settings.CART_SESSION_ID]
        self.save()