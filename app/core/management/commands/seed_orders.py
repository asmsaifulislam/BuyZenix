import random
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import UserProfile
from core.models import Product
from orders.models import Order, OrderItem

REGIONS = [
    {"city": "Dhaka", "state": "Dhaka Division", "country": "Bangladesh"},
    {"city": "Gulshan", "state": "Dhaka Division", "country": "Bangladesh"},
    {"city": "Banani", "state": "Dhaka Division", "country": "Bangladesh"},
    {"city": "Mirpur", "state": "Dhaka Division", "country": "Bangladesh"},
    {"city": "Uttara", "state": "Dhaka Division", "country": "Bangladesh"},
    {"city": "Chattogram", "state": "Chattogram Division", "country": "Bangladesh"},
    {"city": "Cox's Bazar", "state": "Chattogram Division", "country": "Bangladesh"},
    {"city": "Sylhet", "state": "Sylhet Division", "country": "Bangladesh"},
    {"city": "Rajshahi", "state": "Rajshahi Division", "country": "Bangladesh"},
    {"city": "Khulna", "state": "Khulna Division", "country": "Bangladesh"},
    {"city": "Barishal", "state": "Barishal Division", "country": "Bangladesh"},
    {"city": "Rangpur", "state": "Rangpur Division", "country": "Bangladesh"},
    {"city": "Mymensingh", "state": "Mymensingh Division", "country": "Bangladesh"},
    {"city": "Comilla", "state": "Chattogram Division", "country": "Bangladesh"},
    {"city": "Gazipur", "state": "Dhaka Division", "country": "Bangladesh"},
    {"city": "Narayanganj", "state": "Dhaka Division", "country": "Bangladesh"},
    {"city": "Bogra", "state": "Rajshahi Division", "country": "Bangladesh"},
    {"city": "Jessore", "state": "Khulna Division", "country": "Bangladesh"},
    {"city": "Dinajpur", "state": "Rangpur Division", "country": "Bangladesh"},
    {"city": "Tangail", "state": "Dhaka Division", "country": "Bangladesh"},
]

FIRST_NAMES = [
    "Rahim", "Karim", "Jabir", "Hasan", "Farhan", "Tanvir", "Nayeem", "Shakil",
    "Anika", "Tasnim", "Nusrat", "Sabrina", "Maliha", "Farzana", "Roksana",
    "Sumon", "Babul", "Kamal", "Nayeem", "Sohel", "Rubel", "Mizan", "Habib",
    "Aklima", "Shirin", "Nazma", "Rehana", "Monira", "Jesmin", "Lotifa",
    "Arif", "Zahid", "Monir", "Helal", "Belal", "Sohag", "Rimon", "Sabbir",
    "Tanima", "Poly", "Ruma", "Sharmin", "Nasrin", "Mst", "Jahanara", "Rokeya",
]

LAST_NAMES = [
    "Khan", "Hossain", "Rahman", "Islam", "Ahmed", "Uddin", "Miah", "Sheikh",
    "Akter", "Begum", "Parveen", "Khatun", "Nahar", "Jahan", "Lipa",
    "Chowdhury", "Talukder", "Molla", "Sarkar", "Biswas",
    "Mondal", "Gazi", "Howlader", "Sinha", "Debnath",
    "Bhuiyan", "Faruque", "Choudhury", "Rashid", "Mahmud",
]

STATUS_CHOICES = ["pending", "paid", "shipped", "delivered", "cancelled"]
ORDER_COUNT = 300
MONTHS_BACK = 6


class Command(BaseCommand):
    help = "Seed ~300 sample orders across regions with users for the BI dashboard."

    def handle(self, *args, **options):
        now = timezone.now()
        products = list(Product.objects.filter(available=True))
        if not products:
            self.stdout.write(self.style.WARNING("No products. Run 'python manage.py seed' first."))
            return

        # Create customers
        customers = []
        for i in range(40):
            fn = random.choice(FIRST_NAMES)
            ln = random.choice(LAST_NAMES)
            username = f"customer_{fn.lower()}_{i}"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": f"{username}@example.com",
                    "first_name": fn,
                    "last_name": ln,
                },
            )
            if created:
                user.set_password("admin12345")
                user.save()
            UserProfile.objects.get_or_create(user=user, defaults={"role": "customer"})
            customers.append(user)

        # Create some VIP customers (repeat buyers)
        vip_customers = random.sample(customers, min(8, len(customers)))

        self.stdout.write(f"Creating {ORDER_COUNT} orders...")

        for i in range(ORDER_COUNT):
            region = random.choice(REGIONS)
            customer = random.choice(customers)
            days_ago = random.randint(0, 30 * MONTHS_BACK)
            created_dt = now - timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59))
            status = random.choices(STATUS_CHOICES, weights=[10, 25, 20, 35, 10])[0]

            order = Order.objects.create(
                user=customer,
                first_name=customer.first_name,
                last_name=customer.last_name,
                email=customer.email,
                address_line1=f"{random.randint(1, 500)} {random.choice(['Road', 'Street', 'Avenue', 'Lane'])}",
                city=region["city"],
                state=region["state"],
                postal_code=str(random.randint(1000, 9999)),
                country=region["country"],
                phone=f"+8801{random.randint(300000000, 999999999)}",
                paid=status in ("paid", "shipped", "delivered"),
                status=status,
            )
            OrderItem.objects.filter(pk__in=[]).delete()

            # Bypass auto_now_add by using raw insert for backdated orders
            Order.objects.filter(pk=order.pk).update(created=created_dt)

            num_items = random.randint(1, 5)
            order_products = random.sample(products, min(num_items, len(products)))
            for prod in order_products:
                qty = random.randint(1, 4)
                price = prod.effective_price
                item = OrderItem.objects.create(
                    order=order,
                    product=prod,
                    price=price,
                    quantity=qty,
                )

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {ORDER_COUNT} orders across {len(REGIONS)} regions "
            f"with {len(customers)} customers ({len(vip_customers)} VIP)."
        ))
