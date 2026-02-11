from django.urls import reverse 
from django.shortcuts import render, redirect, get_object_or_404
from .models import OrderItem, Order
from .forms import OrderCreateForm
from cart.cart import Cart
from .tasks import order_created
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
import weasyprint
from django.contrib.admin.views.decorators import staff_member_required
from pathlib import Path

def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'admin/orders/order/detail.html', {'order': order})
    
@staff_member_required
def admin_order_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    html = render_to_string('orders/order/pdf.html', {'order': order})
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'filename=order_{order.id}.pdf'
    
    stylesheet_path = Path(settings.STATIC_ROOT) / 'css' / 'pdf.css'
    weasyprint.HTML(string=html).write_pdf(response,
        stylesheets=[weasyprint.CSS(str(stylesheet_path))]) 
    return response
    
def order_create(request):
    cart = Cart(request)
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)  # Crea el objeto Order pero no lo guarda en la BD aún

            if cart.coupon:  # Si el carrito tiene un cupón aplicado
                order.coupon = cart.coupon  # Asigna el cupón a la orden
                order.discount = cart.coupon.discount  # Asigna el descuento del cupón

            order.save()  # Guarda la orden en la base de datos con los datos del cupón
            
            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    price=item['price'],
                    quantity=item['quantity']
                )
            
            # Vaciar el carrito
            cart.clear()
            
            # Lanzar tarea asincrónica
            order_created.delay(order.id)
            
            # Inicializar la orden en sesión
            request.session['order_id'] = order.id 
            
            # Redireccionar al pago
            return redirect(reverse('payment:process'))
            
    else:
        form = OrderCreateForm()
    
    return render(request,
                'orders/order/create.html',
                {'cart': cart, 'form': form})