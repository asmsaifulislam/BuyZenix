from django.contrib import admin, messages
from django.db.models import Count, Q
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.html import format_html

from .models import Category, Product, ProductImage, ProductSize, ProductVariant, ProductRedirect


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "created"]
    prepopulated_fields = {"slug": ["name"]}
    search_fields = ["name"]


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0


class ProductSizeInline(admin.TabularInline):
    model = ProductSize
    extra = 0


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["image_preview", "sku_display", "name", "category", "price", "stock", "available", "featured", "is_archived", "created"]
    list_filter = ["available", "featured", "is_archived", "created", "category", "supplier"]
    list_editable = ["price", "stock", "available", "featured"]
    prepopulated_fields = {"slug": ["name"]}
    search_fields = ["name", "description", "sku", "tags"]
    readonly_fields = ["image_preview", "created", "updated", "archived_at"]
    inlines = [ProductImageInline, ProductSizeInline, ProductVariantInline]
    actions = [
        "action_archive_duplicates",
        "action_restore_archived",
        "action_find_duplicates",
        "action_bulk_make_available",
        "action_bulk_make_unavailable",
        "action_bulk_make_featured",
        "action_bulk_remove_featured",
        "action_generate_skus",
    ]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(supplier=request.user)

    @admin.display(description="Image")
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:48px;height:48px;object-fit:cover;border-radius:8px" />',
                obj.image.url,
            )
        return "-"

    @admin.display(description="SKU")
    def sku_display(self, obj):
        if obj.sku:
            return format_html('<code style="background:#f1f5f9;padding:2px 6px;border-radius:4px;font-size:.78rem">{}</code>', obj.sku)
        return format_html('<span style="color:#9ca3af">—</span>')

    # ── Duplicate Detection ──
    @admin.action(description="🔍 Find duplicates by name")
    def action_find_duplicates(self, request, queryset):
        from django.db.models.functions import Lower
        dupes = (
            Product.objects.values("name")
            .annotate(cnt=Count("id"))
            .filter(cnt__gt=1, is_archived=False)
            .order_by("-cnt")
        )
        count = 0
        for d in dupes:
            count += d["cnt"]
        if count:
            self.message_user(request, f"Found {dupes.count()} duplicate groups ({count} products). Check the product list and archive extras.", messages.WARNING)
        else:
            self.message_user(request, "No duplicates found.", messages.SUCCESS)

    # ── Archive Duplicates ──
    @admin.action(description="📦 Archive selected as duplicates")
    def action_archive_duplicates(self, request, queryset):
        archived = queryset.filter(is_archived=False).update(is_archived=True, archived_at=timezone.now())
        self.message_user(request, f"Archived {archived} product(s). They are hidden from the shop.", messages.SUCCESS)

    # ── Restore Archived ──
    @admin.action(description="♻️ Restore archived products")
    def action_restore_archived(self, request, queryset):
        restored = queryset.filter(is_archived=True).update(is_archived=False, archived_at=None)
        self.message_user(request, f"Restored {restored} product(s).", messages.SUCCESS)

    # ── Bulk Actions ──
    @admin.action(description="✅ Mark available")
    def action_bulk_make_available(self, request, queryset):
        queryset.update(available=True)
        self.message_user(request, f"{queryset.count()} product(s) marked available.", messages.SUCCESS)

    @admin.action(description="❌ Mark unavailable")
    def action_bulk_make_unavailable(self, request, queryset):
        queryset.update(available=False)
        self.message_user(request, f"{queryset.count()} product(s) marked unavailable.", messages.SUCCESS)

    @admin.action(description="⭐ Add to featured")
    def action_bulk_make_featured(self, request, queryset):
        queryset.update(featured=True)
        self.message_user(request, f"{queryset.count()} product(s) added to featured.", messages.SUCCESS)

    @admin.action(description="☆ Remove from featured")
    def action_bulk_remove_featured(self, request, queryset):
        queryset.update(featured=False)
        self.message_user(request, f"{queryset.count()} product(s) removed from featured.", messages.SUCCESS)

    @admin.action(description="🏷️ Auto-generate SKUs")
    def action_generate_skus(self, request, queryset):
        count = 0
        for p in queryset.filter(sku__isnull=True):
            p.sku = f"BZ-{p.id:05d}"
            p.save(update_fields=["sku"])
            count += 1
        self.message_user(request, f"Generated SKUs for {count} product(s).", messages.SUCCESS)


@admin.register(ProductRedirect)
class ProductRedirectAdmin(admin.ModelAdmin):
    list_display = ["old_slug", "new_product", "created"]
    search_fields = ["old_slug", "new_product__name"]
    raw_id_fields = ["new_product"]
