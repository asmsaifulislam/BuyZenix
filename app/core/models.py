from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from .validators import validate_image_file


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.FileField(upload_to="categories/", blank=True, null=True, validators=[validate_image_file])
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "category"
        verbose_name_plural = "categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("core:product_list_by_category", args=[self.slug])

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(
        Category, related_name="products", on_delete=models.CASCADE
    )
    supplier = models.ForeignKey(
        User, related_name="supplier_products", on_delete=models.SET_NULL,
        null=True, blank=True, help_text="Supplier who uploaded this product"
    )
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    sku = models.CharField(max_length=64, unique=True, blank=True, null=True, help_text="Unique SKU for inventory tracking")
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Discounted price (leave empty for no sale)")
    image = models.FileField(upload_to="products/", blank=True, null=True, validators=[validate_image_file])
    video_url = models.URLField(blank=True, help_text="YouTube or Vimeo video URL")
    model_3d = models.FileField(upload_to="products/3d/", blank=True, null=True, help_text="3D model file (.glb, .gltf) for AR/VR viewing")
    stock = models.PositiveIntegerField(default=0)
    available = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False, help_text="Hide product from shop (for duplicate/archive management)")
    archived_at = models.DateTimeField(null=True, blank=True)
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags for organization")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created"]
        indexes = [models.Index(fields=["slug"]), models.Index(fields=["-created"])]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("core:product_detail", args=[self.slug])

    @property
    def effective_price(self):
        if self.sale_price and self.sale_price < self.price:
            return self.sale_price
        return self.price

    @property
    def is_on_sale(self):
        return bool(self.sale_price and self.sale_price < self.price)

    def get_share_urls(self):
        product_url = reverse("core:product_detail", args=[self.slug])
        return {
            "facebook": f"https://www.facebook.com/sharer/sharer.php?u={product_url}",
            "twitter": f"https://twitter.com/intent/tweet?url={product_url}&text={self.name}",
            "whatsapp": f"https://wa.me/?text={self.name}%20{product_url}",
            "linkedin": f"https://www.linkedin.com/sharing/share-offsite/?url={product_url}",
            "telegram": f"https://t.me/share/url?url={product_url}&text={self.name}",
        }

    def __str__(self):
        return self.name


class ProductSize(models.Model):
    product = models.ForeignKey(Product, related_name="sizes", on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True, help_text="Mark to display this size on the product page")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.product.name} - {self.name}"


class ProductImage(models.Model):
    COLOR_CHOICES = [
        ("", "No Color"),
        ("red", "Red"),
        ("blue", "Blue"),
        ("green", "Green"),
        ("black", "Black"),
        ("white", "White"),
        ("yellow", "Yellow"),
        ("purple", "Purple"),
        ("pink", "Pink"),
        ("orange", "Orange"),
        ("gray", "Gray"),
        ("brown", "Brown"),
        ("silver", "Silver"),
        ("gold", "Gold"),
    ]
    ANGLE_CHOICES = [
        ("front", "Front"),
        ("back", "Back"),
        ("left", "Left Side"),
        ("right", "Right Side"),
        ("top", "Top"),
        ("bottom", "Bottom"),
        ("detail", "Detail Close-up"),
        ("lifestyle", "Lifestyle / In Use"),
        ("packaging", "Packaging"),
    ]
    product = models.ForeignKey(
        Product, related_name="gallery", on_delete=models.CASCADE
    )
    image = models.FileField(upload_to="products/gallery/", blank=True, null=True, validators=[validate_image_file])
    color = models.CharField(max_length=20, choices=COLOR_CHOICES, blank=True, default="")
    angle = models.CharField(max_length=20, choices=ANGLE_CHOICES, blank=True, default="front")
    label = models.CharField(max_length=100, blank=True, help_text="Optional label like 'Midnight Blue', 'Matte Finish'")
    position = models.PositiveIntegerField(default=0, help_text="Display order")

    class Meta:
        ordering = ["position"]

    def __str__(self):
        parts = [f"Image for {self.product.name}"]
        if self.color:
            parts.append(self.color)
        if self.angle:
            parts.append(self.angle)
        return " — ".join(parts)


class Wishlist(models.Model):
    user = models.ForeignKey(User, related_name="wishlist", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name="wishlisted_by", on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")
        ordering = ["-created"]

    def __str__(self):
        return f"{self.user.username} — {self.product.name}"


class Review(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    user = models.ForeignKey(User, related_name="reviews", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name="reviews", on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(choices=RATING_CHOICES, default=5)
    title = models.CharField(max_length=120, blank=True)
    body = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]
        unique_together = ("user", "product")

    def __str__(self):
        return f"{self.user.username} — {self.product.name} ({self.rating}★)"

    @property
    def stars(self):
        return "★" * self.rating + "☆" * (5 - self.rating)


class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    excerpt = models.TextField(blank=True, help_text="Short summary for listings")
    body = models.TextField()
    image = models.FileField(upload_to="blog/", blank=True, null=True, validators=[validate_image_file])
    author = models.ForeignKey(User, related_name="blog_posts", on_delete=models.SET_NULL, null=True, blank=True)
    is_published = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("core:blog_detail", args=[self.slug])

    def __str__(self):
        return self.title


class Collection(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.FileField(upload_to="collections/", blank=True, null=True, validators=[validate_image_file])
    products = models.ManyToManyField(Product, blank=True, related_name="collections")
    is_active = models.BooleanField(default=True)
    position = models.PositiveIntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position", "name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("core:collection_detail", args=[self.slug])

    def __str__(self):
        return self.name


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, related_name="variants", on_delete=models.CASCADE)
    name = models.CharField(max_length=100, help_text="e.g. 'Blue / XL' or 'Red / M'")
    sku = models.CharField(max_length=64, unique=True, blank=True, null=True)
    price_override = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Leave empty to use parent price")
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "name"]

    def __str__(self):
        return f"{self.product.name} — {self.name}"

    @property
    def price(self):
        return self.price_override if self.price_override else self.product.effective_price


class ProductRedirect(models.Model):
    old_slug = models.SlugField(max_length=180, unique=True, db_index=True)
    new_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="redirects_from")
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"{self.old_slug} → {self.new_product.slug}"
