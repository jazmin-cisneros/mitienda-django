import redis
from django.conf import settings
from .models import Product

# Conexión a Redis
r = redis.StrictRedis(host=settings.REDIS_HOST,
                     port=settings.REDIS_PORT,
                     db=settings.REDIS_DB)

class Recommender:
    
    def __init__(self):
        self.r = r
    
    def get_product_key(self, id):
        return f'product:{id}:purchased_with'
    
    def products_bought(self, products):
        product_ids = [p.id for p in products]
        for product_id in product_ids:
            for with_id in product_ids:
                if product_id != with_id:
                    self.r.zincrby(
                        name=self.get_product_key(product_id),
                        amount=1,
                        value=str(with_id)
                    )
    
    def suggest_products_for(self, products, max_results=6):
        product_ids = [p.id for p in products]
        
        # Si no hay productos, retornar lista vacía inmediatamente
        if not product_ids:
            return []
            
        if len(product_ids) == 1:
            suggestions = self.r.zrange(
                self.get_product_key(product_ids[0]),
                0, -1, desc=True)[:max_results]
        else:
            flat_ids = ''.join([str(id) for id in product_ids])
            tmp_key = f'tmp_{flat_ids}'
            
            keys = [self.get_product_key(id) for id in product_ids]
            
            # Verificar que hay claves para operar
            if not any(self.r.exists(key) for key in keys):
                return []
                
            self.r.zunionstore(tmp_key, keys)
            self.r.zrem(tmp_key, *product_ids)
            suggestions = self.r.zrange(tmp_key, 0, -1, desc=True)[:max_results]
            self.r.delete(tmp_key)
        
        suggested_products_ids = [int(id) for id in suggestions]
        suggested_products = list(Product.objects.filter(
            id__in=suggested_products_ids))
        
        suggested_products.sort(key=lambda x: suggested_products_ids.index(x.id))
        return suggested_products
    
    def clear_purchases(self):
        for id in Product.objects.values_list('id', flat=True):
            self.r.delete(self.get_product_key(id))