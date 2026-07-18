from django.contrib import admin
from .models import Banner, Page, SiteSettings


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ["title", "is_active", "position", "created"]
    list_filter = ["is_active"]
    list_editable = ["is_active", "position"]


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ["title", "slug", "is_published", "created"]
    list_filter = ["is_published"]
    prepopulated_fields = {"slug": ["title"]}
    search_fields = ["title", "content"]


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ["site_name", "contact_email"]
