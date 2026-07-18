from .cart import Cart


def cart_counts(request):
    if request.session.get("CART_SESSION_ID") is None:
        return {"cart_total_items": 0, "cart_total_price": 0}
    cart = Cart(request)
    return {
        "cart_total_items": cart.get_total_quantity(),
        "cart_total_price": cart.get_total_price(),
    }
