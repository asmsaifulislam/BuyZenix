"""
Management command to clean all test/sample/garbage data.
Preserves: superusers, staff users, SiteSettings, APIKeys, Banners, Pages, Coupons, Promotions.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Category, Product, ProductImage
from orders.models import Order, OrderItem
from accounts.models import UserProfile
from dashboard.models import (
    PageView, AuditLog, LoyaltyPoint, UserActivity,
    ProductRecommendation, ShareLink, Promotion,
    SupplierProfile, PurchaseOrder, PurchaseOrderItem,
    SupplierMetric, Banner, Coupon, APIKey, SiteSettings, Page,
)


class Command(BaseCommand):
    help = "Clean all test/sample data. Preserves superusers, staff, and site config."

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Starting data cleanup..."))

        # === Tier 1: Leaf nodes ===
        share_links = ShareLink.objects.count()
        ShareLink.objects.all().delete()
        self.stdout.write(f"  ShareLinks: {share_links}")

        recs = ProductRecommendation.objects.count()
        ProductRecommendation.objects.all().delete()
        self.stdout.write(f"  ProductRecommendations: {recs}")

        po_items = PurchaseOrderItem.objects.count()
        PurchaseOrderItem.objects.all().delete()
        self.stdout.write(f"  PurchaseOrderItems: {po_items}")

        metrics = SupplierMetric.objects.count()
        SupplierMetric.objects.all().delete()
        self.stdout.write(f"  SupplierMetrics: {metrics}")

        order_items = OrderItem.objects.count()
        OrderItem.objects.all().delete()
        self.stdout.write(f"  OrderItems: {order_items}")

        loyalty = LoyaltyPoint.objects.count()
        LoyaltyPoint.objects.all().delete()
        self.stdout.write(f"  LoyaltyPoints: {loyalty}")

        activities = UserActivity.objects.count()
        UserActivity.objects.all().delete()
        self.stdout.write(f"  UserActivities: {activities}")

        pageviews = PageView.objects.count()
        PageView.objects.all().delete()
        self.stdout.write(f"  PageViews: {pageviews}")

        audits = AuditLog.objects.count()
        AuditLog.objects.all().delete()
        self.stdout.write(f"  AuditLogs: {audits}")

        # === Tier 2: Orders & POs ===
        pos = PurchaseOrder.objects.count()
        PurchaseOrder.objects.all().delete()
        self.stdout.write(f"  PurchaseOrders: {pos}")

        orders = Order.objects.count()
        Order.objects.all().delete()
        self.stdout.write(f"  Orders: {orders}")

        # === Tier 3: Supplier profiles ===
        sps = SupplierProfile.objects.count()
        SupplierProfile.objects.all().delete()
        self.stdout.write(f"  SupplierProfiles: {sps}")

        # === Tier 4: Product images & promotions ===
        imgs = ProductImage.objects.count()
        ProductImage.objects.all().delete()
        self.stdout.write(f"  ProductImages: {imgs}")

        promos = Promotion.objects.count()
        Promotion.objects.all().delete()
        self.stdout.write(f"  Promotions: {promos}")

        # === Tier 5: Products & categories ===
        products = Product.objects.count()
        Product.objects.all().delete()
        self.stdout.write(f"  Products: {products}")

        cats = Category.objects.count()
        Category.objects.all().delete()
        self.stdout.write(f"  Categories: {cats}")

        # === Tier 6: Non-admin users ===
        # Get superuser and staff IDs to preserve
        admin_ids = set(User.objects.filter(is_superuser=True).values_list("id", flat=True))
        staff_ids = set(User.objects.filter(is_staff=True).values_list("id", flat=True))
        preserve_ids = admin_ids | staff_ids

        # Find seed users (customer_* and supplier_*)
        seed_users = User.objects.filter(
            username__startswith=("customer_", "supplier_")
        ).exclude(id__in=preserve_ids)
        seed_count = seed_users.count()

        # Also delete UserProfiles for seed users
        seed_user_ids = list(seed_users.values_list("id", flat=True))
        profile_count = UserProfile.objects.filter(user_id__in=seed_user_ids).delete()[0]

        # Delete seed users
        seed_users.delete()
        self.stdout.write(f"  Seed Users: {seed_count}")
        self.stdout.write(f"  Seed UserProfiles: {profile_count}")

        # Count remaining users
        remaining = User.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f"\nCleanup complete! {remaining} users preserved "
            f"(superusers + staff). All test data removed."
        ))

        # Summary of preserved data
        self.stdout.write(self.style.SUCCESS("\nPreserved:"))
        self.stdout.write(f"  Users: {remaining}")
        self.stdout.write(f"  SiteSettings: {SiteSettings.objects.count()}")
        self.stdout.write(f"  Banners: {Banner.objects.count()}")
        self.stdout.write(f"  Pages: {Page.objects.count()}")
        self.stdout.write(f"  Coupons: {Coupon.objects.count()}")
        self.stdout.write(f"  APIKeys: {APIKey.objects.count()}")
