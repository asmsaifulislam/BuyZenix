from decimal import Decimal

from django.conf import settings
from django.shortcuts import get_object_or_404

from core.models import Product


class Cart:
    """Session-based shopping cart."""

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def _key(self, product, size=""):
        return f"{product.id}|{size}"

    def add(self, product, quantity=1, override_quantity=False, size=""):
        key = self._key(product, size)
        if key not in self.cart:
            self.cart[key] = {
                "quantity": 0,
                "price": str(product.price),
                "size": size,
                "product_id": product.id,
            }
        if override_quantity:
            self.cart[key]["quantity"] = quantity
        else:
            self.cart[key]["quantity"] += quantity
        self.save()

    def remove(self, product, size=""):
        key = self._key(product, size)
        if key in self.cart:
            del self.cart[key]
            self.save()

    def clear(self):
        if settings.CART_SESSION_ID in self.session:
            del self.session[settings.CART_SESSION_ID]
            self.session.modified = True

    def save(self):
        self.session.modified = True

    def __iter__(self):
        product_ids = [item.get("product_id") for item in self.cart.values() if item.get("product_id")]
        products = Product.objects.filter(id__in=product_ids)
        product_map = {p.id: p for p in products}
        for key, item in self.cart.items():
            pid = item.get("product_id", int(key.split("|")[0]))
            item["product"] = product_map.get(pid)
            if item["product"]:
                item["price"] = Decimal(item["price"])
                item["total_price"] = item["price"] * item["quantity"]
                yield item

    def __len__(self):
        return sum(item["quantity"] for item in self.cart.values())

    def get_total_price(self):
        return sum(
            Decimal(item["price"]) * item["quantity"]
            for item in self.cart.values()
        )

    def get_total_quantity(self):
        return self.__len__()
