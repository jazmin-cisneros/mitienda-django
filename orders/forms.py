from django import forms
from .models import Order
from localflavor.us.forms import USZipCodeField  # Importación correcta

class OrderCreateForm(forms.ModelForm):
    postal_code = USZipCodeField()  # ¡Ahora sí con 'p'!
    
    class Meta:
        model = Order
        fields = [
            'first_name', 'last_name', 'email',
            'address', 'postal_code', 'city'
        ]