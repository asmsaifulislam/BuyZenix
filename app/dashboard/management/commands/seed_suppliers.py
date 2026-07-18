import random
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import UserProfile
from core.models import Product
from dashboard.models import (
    PurchaseOrder, PurchaseOrderItem, SupplierMetric, SupplierProfile,
)


SUPPLIERS = [
    {"company": "Dhaka Digital Supply Co.", "country": "Bangladesh", "rating": 4.7, "verified": True},
    {"company": "TechParts Bangladesh Ltd.", "country": "Bangladesh", "rating": 4.3, "verified": True},
    {"company": "FashionHub Bangladesh", "country": "Bangladesh", "rating": 4.5, "verified": True},
    {"company": "HomeZone Manufacturers BD", "country": "Bangladesh", "rating": 3.9, "verified": True},
    {"company": "Chattogram Textile Mills", "country": "Bangladesh", "rating": 4.2, "verified": True},
    {"company": "Sylhet Electronics Ltd.", "country": "Bangladesh", "rating": 4.0, "verified": True},
    {"company": "Rajshahi Garments Pvt.", "country": "Bangladesh", "rating": 3.7, "verified": False},
]

MONTHS_BACK = 6


class Command(BaseCommand):
    help = "Seed supplier profiles, purchase orders, items, and monthly metrics."

    def handle(self, *args, **options):
        now = timezone.now()
        products = list(Product.objects.all())
        if not products:
            self.stdout.write(self.style.WARNING("No products found. Run 'python manage.py seed' first."))
            return

        created_users = []
        for i, s in enumerate(SUPPLIERS):
            username = f"supplier_{i+1}"
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": f"{username}@buyzenix.com",
                    "first_name": s["company"].split()[0],
                    "last_name": " ".join(s["company"].split()[1:]),
                },
            )
            if _:
                user.set_password("admin12345")
                user.save()
            UserProfile.objects.get_or_create(
                user=user, defaults={"role": "supplier", "company_name": s["company"]}
            )
            profile, _ = SupplierProfile.objects.get_or_create(
                user=user,
                defaults={
                    "company_name": s["company"],
                    "contact_email": f"{username}@buyzenix.com",
                    "contact_phone": f"+8801{random.randint(300000000, 999999999)}",
                    "country": s["country"],
                    "is_verified": s["verified"],
                    "rating": s["rating"],
                },
            )
            created_users.append((user, profile))

        statuses = ["delivered", "delivered", "delivered", "delivered", "shipped", "confirmed", "cancelled"]

        for user, profile in created_users:
            for months_ago in range(MONTHS_BACK, -1, -1):
                month_date = (now - timedelta(days=30 * months_ago)).replace(day=1)
                num_orders = random.randint(2, 6)

                total_spend = Decimal("0")
                on_time = 0
                total_deliveries = 0
                defective = 0
                total_items = 0
                lead_times = []

                for _ in range(num_orders):
                    status = random.choice(statuses)
                    order_num = f"PO-{random.randint(100000, 999999)}"
                    expected = (month_date + timedelta(days=random.randint(10, 30))).date()
                    created_dt = month_date + timedelta(days=random.randint(0, 15))

                    actual = None
                    is_on_time = None
                    if status == "delivered":
                        offset = random.randint(-3, 5)
                        actual = expected + timedelta(days=offset)
                        is_on_time = offset <= 0
                        lead_times.append((actual - created_dt.date()).days)
                        total_deliveries += 1
                        if is_on_time:
                            on_time += 1

                    po = PurchaseOrder.objects.create(
                        supplier=profile,
                        order_number=order_num,
                        status=status,
                        expected_delivery=expected,
                        actual_delivery=actual,
                        is_on_time=is_on_time,
                    )

                    num_items = random.randint(1, 4)
                    po_products = random.sample(products, min(num_items, len(products)))
                    for prod in po_products:
                        qty = random.randint(5, 100)
                        cost = (prod.price * Decimal(str(round(random.uniform(0.3, 0.7), 2)))).quantize(Decimal("0.01"))
                        rec_qty = qty if status == "delivered" else 0
                        is_def = random.random() < 0.08
                        if is_def and rec_qty > 0:
                            defective += rec_qty
                        total_items += rec_qty
                        PurchaseOrderItem.objects.create(
                            purchase_order=po,
                            product=prod,
                            quantity=qty,
                            unit_cost=cost,
                            received_quantity=rec_qty,
                            is_defective=is_def,
                        )

                    po.calculate_total()
                    if status in ("delivered", "cancelled", "shipped", "confirmed"):
                        total_spend += po.total_amount or Decimal("0")

                avg_lead = round(sum(lead_times) / len(lead_times), 1) if lead_times else 0

                SupplierMetric.objects.update_or_create(
                    supplier=profile,
                    month=month_date,
                    defaults={
                        "total_orders": num_orders,
                        "on_time_deliveries": on_time,
                        "total_deliveries": total_deliveries,
                        "defective_items": defective,
                        "total_items_received": total_items,
                        "total_spend": total_spend,
                        "avg_lead_time_days": avg_lead,
                    },
                )

        self.stdout.write(self.style.SUCCESS("Supplier sample data seeded successfully."))
