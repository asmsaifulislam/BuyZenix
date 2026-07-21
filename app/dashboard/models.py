from django.db import models

from core.validators import validate_image_file


class Page(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    content = models.TextField(blank=True, help_text="HTML content for the page")
    meta_description = models.CharField(max_length=300, blank=True)
    is_published = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return self.title


class Banner(models.Model):
    title = models.CharField(max_length=200)
    image = models.FileField(upload_to="banners/", blank=True, null=True, validators=[validate_image_file])
    link_url = models.URLField(blank=True, help_text="URL to link to when clicked")
    is_active = models.BooleanField(default=True)
    position = models.PositiveIntegerField(default=0, help_text="Display order")
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position", "-created"]
        verbose_name_plural = "banners"

    def __str__(self):
        return self.title


class SiteSettings(models.Model):
    site_name = models.CharField(max_length=200, default="BuyZenix")
    site_tagline = models.CharField(max_length=300, blank=True, default="Premium Online Store")
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    logo = models.FileField(upload_to="site/", blank=True, null=True, validators=[validate_image_file])
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        if not self.pk and SiteSettings.objects.exists():
            raise ValueError("Only one SiteSettings instance is allowed.")
        super().save(*args, **kwargs)


class APIKey(models.Model):
    CATEGORY_CHOICES = [
        ("payment", "Payment Gateway"),
        ("bi", "Business Intelligence"),
        ("seo", "SEO Tools"),
        ("chatbot", "Chatbot / AI"),
        ("tracking", "User Tracking / Analytics"),
        ("email", "Email Service"),
        ("sms", "SMS Service"),
        ("cdn", "CDN / Media"),
    ]
    name = models.CharField(max_length=150)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default="payment")
    api_key = models.CharField(max_length=500, blank=True, help_text="Enter API key or secret")
    api_secret = models.CharField(max_length=500, blank=True, help_text="Optional: API secret or secondary key")
    endpoint = models.URLField(blank=True, help_text="Optional: API endpoint URL")
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True, help_text="What this API key is used for")
    last_tested = models.DateTimeField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category", "name"]

    def __str__(self):
        return f"[{self.get_category_display()}] {self.name}"


class Coupon(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ("percent", "Percentage (%)"),
        ("fixed", "Fixed Amount"),
    ]
    code = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=250, blank=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES, default="percent")
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, help_text="Percentage or fixed amount")
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_uses = models.PositiveIntegerField(default=0, help_text="0 = unlimited")
    used_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_to = models.DateTimeField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"{self.code} ({self.discount_value}{ '%' if self.discount_type == 'percent' else ''})"

    def is_valid(self):
        from django.utils import timezone
        now = timezone.now()
        if not self.is_active:
            return False
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_to and now > self.valid_to:
            return False
        if self.max_uses > 0 and self.used_count >= self.max_uses:
            return False
        return True

    def apply_discount(self, amount):
        if self.discount_type == "percent":
            return amount * (self.discount_value / 100)
        return min(self.discount_value, amount)


class PageView(models.Model):
    url = models.CharField(max_length=500)
    product = models.ForeignKey("core.Product", null=True, blank=True, on_delete=models.SET_NULL, related_name="page_views")
    user = models.ForeignKey("auth.User", null=True, blank=True, on_delete=models.SET_NULL)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    referrer = models.CharField(max_length=500, blank=True)
    session_key = models.CharField(max_length=100, blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-viewed_at"]

    def __str__(self):
        return f"{self.url} — {self.viewed_at}"


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ("create", "Create"),
        ("update", "Update"),
        ("delete", "Delete"),
        ("login", "Login"),
        ("logout", "Logout"),
        ("order", "Order"),
    ]
    user = models.ForeignKey("auth.User", null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=100, blank=True)
    object_repr = models.CharField(max_length=300, blank=True)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"[{self.action}] {self.model_name} by {self.user}"


class LoyaltyPoint(models.Model):
    user = models.ForeignKey("auth.User", related_name="loyalty_points", on_delete=models.CASCADE)
    points = models.PositiveIntegerField(default=0)
    reason = models.CharField(max_length=255, blank=True)
    order = models.ForeignKey("orders.Order", null=True, blank=True, on_delete=models.SET_NULL)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"{self.user.username}: +{self.points} pts"

    @classmethod
    def get_balance(cls, user):
        return cls.objects.filter(user=user).aggregate(
            total=models.Sum("points")
        )["total"] or 0

    @classmethod
    def earn_for_order(cls, user, order):
        total = order.get_total_cost()
        points = int(float(total))
        if points > 0:
            cls.objects.create(user=user, points=points, reason=f"Order #{order.id}", order=order)


class UserActivity(models.Model):
    user = models.ForeignKey("auth.User", related_name="activities", on_delete=models.CASCADE)
    product = models.ForeignKey("core.Product", null=True, blank=True, on_delete=models.SET_NULL)
    activity_type = models.CharField(max_length=30, choices=[
        ("view", "Product View"),
        ("cart", "Add to Cart"),
        ("purchase", "Purchase"),
        ("share", "Share"),
        ("review", "Review"),
    ])
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"{self.user.username} - {self.activity_type}"


class ProductRecommendation(models.Model):
    source_product = models.ForeignKey("core.Product", related_name="recommended_from", on_delete=models.CASCADE)
    recommended_product = models.ForeignKey("core.Product", related_name="recommended_to", on_delete=models.CASCADE)
    score = models.FloatField(default=0.0)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-score"]
        unique_together = ["source_product", "recommended_product"]

    def __str__(self):
        return f"{self.source_product.name} -> {self.recommended_product.name} ({self.score})"


class ShareLink(models.Model):
    product = models.ForeignKey("core.Product", related_name="share_links", on_delete=models.CASCADE)
    platform = models.CharField(max_length=30, choices=[
        ("facebook", "Facebook"),
        ("twitter", "Twitter/X"),
        ("whatsapp", "WhatsApp"),
        ("linkedin", "LinkedIn"),
        ("telegram", "Telegram"),
        ("instagram", "Instagram"),
    ])
    url = models.URLField()
    clicks = models.PositiveIntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-clicks"]

    def __str__(self):
        return f"{self.product.name} - {self.platform}"


class Promotion(models.Model):
    POSITION_CHOICES = [
        ("hero_left", "Hero Left"),
        ("hero_right", "Hero Right"),
        ("below_hero", "Below Hero"),
    ]
    title = models.CharField(max_length=200, help_text="e.g. Eid Special Offer")
    subtitle = models.CharField(max_length=300, blank=True, help_text="e.g. 30% OFF on all products")
    discount_text = models.CharField(max_length=50, blank=True, help_text="e.g. 30% OFF")
    product = models.ForeignKey("core.Product", null=True, blank=True, on_delete=models.SET_NULL, help_text="Featured product to show")
    bg_color = models.CharField(max_length=30, default="#4f46e5", help_text="Background color hex code")
    text_color = models.CharField(max_length=30, default="#ffffff", help_text="Text color hex code")
    button_text = models.CharField(max_length=50, blank=True, help_text="e.g. Shop Now")
    button_url = models.CharField(max_length=300, blank=True, help_text="e.g. /products/ or /products/slug/")
    position = models.CharField(max_length=20, choices=POSITION_CHOICES, default="hero_left")
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "-created"]

    def __str__(self):
        return self.title


# ─── Supplier Dashboard Models ───


class SupplierProfile(models.Model):
    user = models.OneToOneField("auth.User", on_delete=models.CASCADE, related_name="supplier_profile")
    company_name = models.CharField(max_length=200)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    country = models.CharField(max_length=100, default="Bangladesh")
    is_verified = models.BooleanField(default=False)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0, help_text="1-5 rating")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return self.company_name


class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("sent", "Sent"),
        ("confirmed", "Confirmed"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]
    supplier = models.ForeignKey(SupplierProfile, on_delete=models.CASCADE, related_name="purchase_orders")
    order_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    expected_delivery = models.DateField(null=True, blank=True)
    actual_delivery = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    is_on_time = models.BooleanField(null=True, blank=True, help_text="Was it delivered on or before expected date?")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"PO-{self.order_number}"

    def calculate_total(self):
        total = sum(item.subtotal for item in self.items.all())
        self.total_amount = total
        self.save(update_fields=["total_amount"])
        return total


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("core.Product", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    received_quantity = models.PositiveIntegerField(default=0, help_text="Actual quantity received")
    is_defective = models.BooleanField(default=False)
    defect_notes = models.TextField(blank=True)

    class Meta:
        ordering = ["pk"]

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"

    @property
    def subtotal(self):
        return self.unit_cost * self.quantity


class SupplierMetric(models.Model):
    supplier = models.ForeignKey(SupplierProfile, on_delete=models.CASCADE, related_name="metrics")
    month = models.DateField(help_text="First day of the month this metric covers")
    total_orders = models.PositiveIntegerField(default=0)
    on_time_deliveries = models.PositiveIntegerField(default=0)
    total_deliveries = models.PositiveIntegerField(default=0)
    defective_items = models.PositiveIntegerField(default=0)
    total_items_received = models.PositiveIntegerField(default=0)
    total_spend = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    avg_lead_time_days = models.FloatField(default=0, help_text="Average days between order and delivery")
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-month"]
        unique_together = ["supplier", "month"]

    def __str__(self):
        return f"{self.supplier.company_name} - {self.month.strftime('%b %Y')}"

    @property
    def on_time_rate(self):
        if self.total_deliveries == 0:
            return 0
        return round((self.on_time_deliveries / self.total_deliveries) * 100, 1)

    @property
    def defect_rate(self):
        if self.total_items_received == 0:
            return 0
        return round((self.defective_items / self.total_items_received) * 100, 1)
