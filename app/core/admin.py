from django.contrib import admin
from django.utils.html import format_html

from .models import Category, Product, ProductImage


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "created"]
    prepopulated_fields = {"slug": ["name"]}
    search_fields = ["name"]


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["image_preview", "name", "category", "supplier", "price", "stock", "available", "featured", "created"]
    list_filter = ["available", "featured", "created", "category", "supplier"]
    list_editable = ["price", "stock", "available", "featured"]
    prepopulated_fields = {"slug": ["name"]}
    search_fields = ["name", "description"]
    readonly_fields = ["image_preview", "created", "updated"]
    inlines = [ProductImageInline]

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
