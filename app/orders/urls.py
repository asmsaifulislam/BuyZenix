from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),
    path("buy-now/<int:product_id>/", views.buy_now, name="buy_now"),
    path("complete/<int:order_id>/", views.order_complete, name="order_complete"),
    path("order/<int:order_id>/", views.order_detail, name="order_detail"),
]
