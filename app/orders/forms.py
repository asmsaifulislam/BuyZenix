from django import forms


class OrderCreateForm(forms.Form):
    first_name = forms.CharField(max_length=60)
    last_name = forms.CharField(max_length=60)
    email = forms.EmailField()
    address_line1 = forms.CharField(max_length=200)
    address_line2 = forms.CharField(max_length=200, required=False)
    city = forms.CharField(max_length=100)
    state = forms.CharField(max_length=100, required=False)
    postal_code = forms.CharField(max_length=20)
    country = forms.CharField(max_length=100)
    phone = forms.CharField(max_length=30, required=False)
