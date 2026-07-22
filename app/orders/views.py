from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from core.models import Product
from cart.cart import Cart

from .forms import OrderCreateForm
from .models import Order, OrderItem
from .tasks import order_created


def checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        return redirect("core:product_list")

    if request.method == "POST":
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                **form.cleaned_data,
            )
            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item["product"],
                    price=item["price"],
                    quantity=item["quantity"],
                    size=item.get("size", ""),
                )
            cart.clear()
            try:
                order_created.delay(order.id)
            except Exception:
                pass
            request.session["order_id"] = order.id
            return redirect("orders:order_complete", order_id=order.id)
    else:
        initial = {}
        if request.user.is_authenticated:
            u = request.user
            profile = getattr(u, "profile", None)
            initial = {
                "first_name": u.first_name,
                "last_name": u.last_name,
                "email": u.email,
            }
            if profile:
                initial.update(
                    {
                        "address_line1": profile.address_line1,
                        "address_line2": profile.address_line2,
                        "city": profile.city,
                        "state": profile.state,
                        "postal_code": profile.postal_code,
                        "country": profile.country,
                        "phone": profile.phone,
                    }
                )
        form = OrderCreateForm(initial=initial)

    return render(
        request, "orders/checkout.html", {"cart": cart, "form": form}
    )


def buy_now(request, product_id):
    product = get_object_or_404(Product, id=product_id, available=True)
    quantity = 1
    if request.method == "POST":
        quantity = int(request.POST.get("quantity", 1))
        full_name = request.POST.get("full_name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        address_line1 = request.POST.get("address_line1", "").strip()
        city = request.POST.get("city", "").strip()
        state = request.POST.get("state", "").strip()
        postal_code = request.POST.get("postal_code", "").strip()
        country = request.POST.get("country", "").strip()

        errors = {}
        if not full_name:
            errors["full_name"] = ["Required"]
        if not email:
            errors["email"] = ["Required"]
        if not phone:
            errors["phone"] = ["Required"]
        if not address_line1:
            errors["address_line1"] = ["Required"]
        if not city:
            errors["city"] = ["Required"]
        if not postal_code:
            errors["postal_code"] = ["Required"]
        if not country:
            errors["country"] = ["Required"]

        if errors:
            return render(request, "orders/buy_now.html", {
                "product": product,
                "quantity": quantity,
                "total_price": product.price * quantity,
                "form_data": request.POST,
                "errors": errors,
            })

        name_parts = full_name.split(" ", 1)
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            first_name=name_parts[0],
            last_name=name_parts[1] if len(name_parts) > 1 else "",
            email=email,
            phone=phone,
            address_line1=address_line1,
            city=city,
            state=state,
            postal_code=postal_code,
            country=country,
        )
        OrderItem.objects.create(
            order=order,
            product=product,
            price=product.price,
            quantity=quantity,
            size=request.POST.get("size", "").strip(),
        )
        try:
            order_created.delay(order.id)
        except Exception:
            pass
        request.session["order_id"] = order.id
        return redirect("orders:order_complete", order_id=order.id)

    return render(request, "orders/buy_now.html", {
        "product": product,
        "quantity": quantity,
        "total_price": product.price * quantity,
    })


def order_complete(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, "orders/order_complete.html", {"order": order})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, "orders/order_detail.html", {"order": order})
