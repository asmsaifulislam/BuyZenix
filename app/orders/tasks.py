from celery import shared_task
from django.core.mail import mail_admins, send_mail

from .models import Order


@shared_task
def order_created(order_id):
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return

    subject = f"BuyZenix — Order #{order.id} confirmation"
    message = (
        f"Hi {order.first_name},\n\n"
        f"Thanks for shopping with BuyZenix!\n"
        f"Your order #{order.id} has been received and is being processed.\n\n"
        f"Total: ${order.get_total_cost()}\n\n"
        f"We'll notify you when it ships.\n\n"
        f"— The BuyZenix Team"
    )
    send_mail(
        subject,
        message,
        None,
        [order.email],
        fail_silently=True,
    )
    mail_admins(
        f"New order #{order.id}",
        f"Order #{order.id} placed by {order.email} for ${order.get_total_cost()}.",
        fail_silently=True,
    )
    return order_id
