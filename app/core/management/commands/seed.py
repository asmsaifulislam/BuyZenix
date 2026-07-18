import random

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from core.models import Category, Product


SAMPLE = [
    ("Electronics", [
        ("ZenBook Pro 14", "Ultra-slim laptop with vivid display and all-day battery.", 129900.00, 12),
        ("Aurora Wireless Earbuds", "Immersive sound with active noise cancellation.", 1490.00, 40),
        ("Pulse Smartwatch", "Track health, fitness and notifications on your wrist.", 2490.00, 25),
        ("Nimbus Mechanical Keyboard", "Tactile RGB keyboard built for creators.", 1890.00, 60),
    ]),
    ("Fashion", [
        ("Cloud Hoodie", "Premium cotton hoodie with a zen fit.", 1590.00, 80),
        ("Stride Sneakers", "Lightweight everyday sneakers in midnight blue.", 3190.00, 35),
        ("Vortex Cap", "Minimalist cap with embroidered logo.", 590.00, 100),
    ]),
    ("Home", [
        ("Lumen Smart Lamp", "Ambient lighting controlled from your phone.", 1290.00, 50),
        ("Terra Ceramic Mug", "Hand-glazed mug for your mindful mornings.", 490.00, 120),
        ("Hush Diffuser", "Quiet aroma diffuser for calm spaces.", 990.00, 45),
    ]),
    ("Accessories", [
        ("Flux Power Bank", "20,000mAh fast-charge power bank.", 1450.00, 70),
        ("Echo Braided Cable", "Durable USB-C cable, 2m.", 450.00, 150),
    ]),
]


class Command(BaseCommand):
    help = "Seed the catalog with sample categories and products."

    def handle(self, *args, **options):
        for cat_name, products in SAMPLE:
            category, _ = Category.objects.get_or_create(
                name=cat_name, defaults={"slug": slugify(cat_name)}
            )
            for name, desc, price, stock in products:
                Product.objects.update_or_create(
                    slug=slugify(name),
                    defaults={
                        "category": category,
                        "name": name,
                        "description": desc,
                        "price": price,
                        "stock": stock,
                        "available": True,
                        "featured": random.choice([True, False]),
                    },
                )
        self.stdout.write(self.style.SUCCESS("Seeded catalog successfully."))
