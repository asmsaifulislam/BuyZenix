from decimal import Decimal

from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.models import Product
from .cart import Cart


@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id, available=True)
    quantity = int(request.POST.get("quantity", 1))
    override = request.POST.get("override") == "true"
    size = request.POST.get("size", "").strip()
    cart.add(product, quantity=quantity, override_quantity=override, size=size)
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return render(request, "cart/cart_dropdown.html", {"cart": cart})
    return redirect("cart:cart_detail")


@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    size = request.POST.get("size", "").strip()
    cart.remove(product, size=size)
    return redirect("cart:cart_detail")


def cart_clear(request):
    cart = Cart(request)
    cart.clear()
    return redirect("cart:cart_detail")


@require_POST
def cart_update_quantity(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    size = request.POST.get("size", "").strip()
    quantity = int(request.POST.get("quantity", 1))
    if quantity < 1:
        quantity = 1
    cart.add(product, quantity=quantity, override_quantity=True, size=size)
    return redirect("cart:cart_detail")


def cart_detail(request):
    cart = Cart(request)
    coupon_code = request.session.get("coupon_code", "")
    coupon_discount = request.session.get("coupon_discount", 0)
    for item in cart:
        item["update_quantity_form"] = None

    subtotal = sum(item["price"] * item["quantity"] for item in cart)
    discount = Decimal(str(coupon_discount))
    total = max(subtotal - discount, Decimal("0"))

    return render(request, "cart/cart_detail.html", {
        "cart": cart,
        "coupon_code": coupon_code,
        "coupon_discount": discount,
        "subtotal": subtotal,
        "total": total,
    })


@require_POST
def cart_apply_coupon(request):
    code = request.POST.get("coupon_code", "").strip().upper()
    if not code:
        return redirect("cart:cart_detail")

    from dashboard.models import Coupon
    try:
        coupon = Coupon.objects.get(code=code)
    except Coupon.DoesNotExist:
        return render(request, "cart/cart_detail.html", {
            "cart": Cart(request),
            "coupon_error": "Invalid coupon code.",
            "subtotal": sum(i["price"] * i["quantity"] for i in Cart(request)),
        })

    if not coupon.is_valid():
        return render(request, "cart/cart_detail.html", {
            "cart": Cart(request),
            "coupon_error": "This coupon is expired or fully used.",
            "subtotal": sum(i["price"] * i["quantity"] for i in Cart(request)),
        })

    cart = Cart(request)
    subtotal = sum(item["price"] * item["quantity"] for item in cart)

    if subtotal < float(coupon.min_order_amount):
        return render(request, "cart/cart_detail.html", {
            "cart": cart,
            "coupon_error": f"Minimum order ${coupon.min_order_amount} required.",
            "subtotal": subtotal,
        })

    discount = float(coupon.apply_discount(subtotal))
    coupon.used_count += 1
    coupon.save(update_fields=["used_count"])

    request.session["coupon_code"] = coupon.code
    request.session["coupon_discount"] = discount
    return redirect("cart:cart_detail")


@require_POST
def cart_remove_coupon(request):
    request.session.pop("coupon_code", None)
    request.session.pop("coupon_discount", None)
    return redirect("cart:cart_detail")
