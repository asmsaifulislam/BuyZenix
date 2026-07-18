from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.timezone import now
from datetime import timedelta


class BuyZenixAdminSite(AdminSite):
    site_header = "BuyZenix Administration"
    site_title = "BuyZenix Admin"
    index_title = "Dashboard"
    enable_nav_sidebar = True

    def index(self, request, extra_context=None):
        from django.db.models import Count, Sum
        from django.db.models.functions import TruncDate
        from core.models import Product, Category
        from orders.models import Order, OrderItem
        from django.contrib.auth.models import User
        from accounts.models import UserProfile
        import json

        ctx = {}
        ctx["total_orders"] = Order.objects.count()
        total_revenue = OrderItem.objects.aggregate(total=Sum("price"))["total"] or 0
        ctx["total_revenue"] = f"\u09f3{total_revenue:,.2f}" if total_revenue else "\u09f30.00"
        ctx["total_products"] = Product.objects.count()
        ctx["active_products"] = Product.objects.filter(available=True).count()
        ctx["total_users"] = User.objects.count()
        ctx["total_suppliers"] = UserProfile.objects.filter(role="supplier").count()

        ctx["recent_orders"] = Order.objects.order_by("-created")[:8]

        ctx["top_products"] = (
            OrderItem.objects.values("product__name")
            .annotate(total_sold=Count("id"), total_revenue=Sum("price"))
            .order_by("-total_revenue")[:5]
        )

        ctx["low_stock"] = Product.objects.filter(stock__lte=5, available=True).order_by("stock")[:8]

        last_30 = now() - timedelta(days=30)
        daily_qs = (
            Order.objects.filter(created__gte=last_30)
            .annotate(date=TruncDate("created"))
            .values("date")
            .annotate(count=Count("id"), revenue=Sum("items__price"))
            .order_by("date")
        )
        ctx["daily_orders"] = json.dumps([
            {"date": d["date"].strftime("%Y-%m-%d") if d["date"] else "",
             "count": d["count"],
             "revenue": float(d["revenue"]) if d["revenue"] else 0}
            for d in daily_qs
        ])

        status_qs = Order.objects.values("status").annotate(count=Count("id")).order_by("status")
        ctx["status_dist"] = json.dumps([
            {"status": s["status"], "count": s["count"]} for s in status_qs
        ])

        if extra_context:
            ctx.update(extra_context)

        return super().index(request, extra_context=ctx)


admin_site = BuyZenixAdminSite(name="buyzenix_admin")


from django.contrib.auth.models import User, Group
from core.models import Product, Category, ProductImage
from orders.models import Order, OrderItem
from accounts.models import UserProfile
from dashboard.models import Banner, Page, SiteSettings, APIKey, Coupon, PageView, AuditLog, LoyaltyPoint, UserActivity, ProductRecommendation, ShareLink


class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "stock", "available", "featured")
    list_filter = ("available", "featured", "category")
    search_fields = ("name",)


class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    prepopulated_fields = {"slug": ("name",)}


class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "first_name", "last_name", "email", "status", "created")
    list_filter = ("status", "paid")


class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "price", "quantity")


class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_type", "discount_value", "is_active", "used_count")


class APIKeyAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "is_active")


class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("user", "action", "model_name", "timestamp")


class BannerAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "position")


class PageAdmin(admin.ModelAdmin):
    list_display = ("title", "is_published")


admin_site.register(User)
admin_site.register(Group)
admin_site.register(Product, ProductAdmin)
admin_site.register(Category, CategoryAdmin)
admin_site.register(ProductImage)
admin_site.register(Order, OrderAdmin)
admin_site.register(OrderItem, OrderItemAdmin)
admin_site.register(UserProfile)
admin_site.register(Banner, BannerAdmin)
admin_site.register(Page, PageAdmin)
admin_site.register(SiteSettings)
admin_site.register(APIKey, APIKeyAdmin)
admin_site.register(Coupon, CouponAdmin)
admin_site.register(PageView)
admin_site.register(AuditLog, AuditLogAdmin)
admin_site.register(LoyaltyPoint)
admin_site.register(UserActivity)
admin_site.register(ProductRecommendation)
admin_site.register(ShareLink)
