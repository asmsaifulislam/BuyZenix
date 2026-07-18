from django.urls import path
from . import views
from .engagement import track_engagement
from .gdpr import gdpr_data_export, gdpr_data_export_csv, gdpr_delete_account, cookie_consent_save, privacy_policy
from .rbac import rbac_groups, rbac_group_create, rbac_group_edit, rbac_group_delete
from .reporting import report_revenue, report_products, report_users, report_plotly_chart
from .chatbot_api import chatbot_api

app_name = "dashboard"

urlpatterns = [
    # Supplier
    path("supplier/", views.supplier_dashboard, name="supplier_dashboard"),
    path("supplier/products/", views.supplier_product_list, name="supplier_products"),
    path("supplier/products/create/", views.supplier_product_create, name="supplier_product_create"),
    path("supplier/products/<int:pk>/edit/", views.supplier_product_edit, name="supplier_product_edit"),
    path("supplier/products/<int:pk>/delete/", views.supplier_product_delete, name="supplier_product_delete"),
    path("supplier/gallery/<int:pk>/delete/", views.supplier_gallery_delete, name="supplier_gallery_delete"),
    # Admin
    path("", views.admin_bi_dashboard, name="admin_bi"),
    path("users/", views.admin_user_list, name="admin_users"),
    path("users/<int:pk>/edit/", views.admin_user_edit, name="admin_user_edit"),
    path("users/<int:pk>/toggle/", views.admin_user_toggle, name="admin_user_toggle"),
    path("products/", views.admin_product_list, name="admin_products"),
    path("products/create/", views.admin_product_create, name="admin_product_create"),
    path("products/<int:pk>/edit/", views.admin_product_edit, name="admin_product_edit"),
    path("products/<int:pk>/delete/", views.admin_product_delete, name="admin_product_delete"),
    path("products/gallery/<int:pk>/delete/", views.admin_product_gallery_delete, name="admin_product_gallery_delete"),
    path("categories/", views.admin_category_list, name="admin_categories"),
    path("categories/<int:pk>/delete/", views.admin_category_delete, name="admin_category_delete"),
    path("banners/", views.admin_banner_list, name="admin_banners"),
    path("banners/create/", views.admin_banner_create, name="admin_banner_create"),
    path("banners/<int:pk>/edit/", views.admin_banner_edit, name="admin_banner_edit"),
    path("banners/<int:pk>/delete/", views.admin_banner_delete, name="admin_banner_delete"),
    path("pages/", views.admin_page_list, name="admin_pages"),
    path("pages/create/", views.admin_page_create, name="admin_page_create"),
    path("pages/<int:pk>/edit/", views.admin_page_edit, name="admin_page_edit"),
    path("pages/<int:pk>/delete/", views.admin_page_delete, name="admin_page_delete"),
    path("settings/", views.admin_site_settings, name="admin_settings"),
    # API Keys
    path("api-keys/", views.admin_api_keys, name="admin_api_keys"),
    path("api-keys/create/", views.admin_api_key_create, name="admin_api_key_create"),
    path("api-keys/<int:pk>/edit/", views.admin_api_key_edit, name="admin_api_key_edit"),
    path("api-keys/<int:pk>/delete/", views.admin_api_key_delete, name="admin_api_key_delete"),
    path("api-keys/<int:pk>/toggle/", views.admin_api_key_toggle, name="admin_api_key_toggle"),
    # Coupons
    path("coupons/", views.admin_coupon_list, name="admin_coupons"),
    path("coupons/create/", views.admin_coupon_create, name="admin_coupon_create"),
    path("coupons/<int:pk>/edit/", views.admin_coupon_edit, name="admin_coupon_edit"),
    path("coupons/<int:pk>/delete/", views.admin_coupon_delete, name="admin_coupon_delete"),
    # Audit Logs
    path("audit-logs/", views.admin_audit_logs, name="admin_audit_logs"),
    # Share API
    path("share-api/", views.admin_share_api, name="admin_share_api"),
    # Recommendations
    path("recommendations/", views.admin_recommendations, name="admin_recommendations"),
    path("recommendations/create/", views.admin_recommendation_create, name="admin_recommendation_create"),
    path("recommendations/<int:pk>/delete/", views.admin_recommendation_delete, name="admin_recommendation_delete"),
    # Loyalty
    path("loyalty/", views.admin_loyalty, name="admin_loyalty"),
    # Promotions
    path("promotions/", views.admin_promotions, name="admin_promotions"),
    path("promotions/create/", views.admin_promotion_create, name="admin_promotion_create"),
    path("promotions/<int:pk>/edit/", views.admin_promotion_edit, name="admin_promotion_edit"),
    path("promotions/<int:pk>/delete/", views.admin_promotion_delete, name="admin_promotion_delete"),
    path("promotions/<int:pk>/toggle/", views.admin_promotion_toggle, name="admin_promotion_toggle"),
    # Supplier Performance
    path("supplier-performance/", views.admin_supplier_performance, name="admin_supplier_performance"),
    # Customer Report
    path("customer-report/", views.admin_customer_report, name="admin_customer_report"),
    # Sale Report
    path("sale-report/", views.admin_sale_report, name="admin_sale_report"),
    # Product Report
    path("product-report/", views.admin_product_report, name="admin_product_report"),
    # Marketing Report
    path("marketing-report/", views.admin_marketing_report, name="admin_marketing_report"),
    # Operations Report
    path("operations-report/", views.admin_operations_report, name="admin_operations_report"),
    # Finance Report
    path("finance-report/", views.admin_finance_report, name="admin_finance_report"),
    # VAT & Tax Report
    path("tax-report/", views.admin_tax_report, name="admin_tax_report"),
    # Product Demand Dashboard
    path("demand-report/", views.admin_demand_report, name="admin_demand_report"),
    # RBAC
    path("rbac/", rbac_groups, name="rbac_groups"),
    path("rbac/create/", rbac_group_create, name="rbac_group_create"),
    path("rbac/<int:pk>/edit/", rbac_group_edit, name="rbac_group_edit"),
    path("rbac/<int:pk>/delete/", rbac_group_delete, name="rbac_group_delete"),
    # Reporting / Exports
    path("reports/revenue/", report_revenue, name="report_revenue"),
    path("reports/products/", report_products, name="report_products"),
    path("reports/users/", report_users, name="report_users"),
    path("charts/", report_plotly_chart, name="report_plotly_chart"),
    # GDPR / Privacy
    path("privacy/", privacy_policy, name="privacy_policy"),
    path("my-data/", gdpr_data_export, name="gdpr_data_export"),
    path("my-data/csv/", gdpr_data_export_csv, name="gdpr_data_export_csv"),
    path("delete-account/", gdpr_delete_account, name="gdpr_delete_account"),
]
