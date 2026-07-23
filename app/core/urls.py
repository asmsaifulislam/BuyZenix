from django.urls import path
from django.views.generic import TemplateView

from . import views
from dashboard.engagement import track_engagement
from dashboard.gdpr import gdpr_data_export, gdpr_data_export_csv, gdpr_delete_account, cookie_consent_save
from dashboard.chatbot_api import chatbot_api

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("set-currency/", views.set_currency, name="set_currency"),
    path("products/", views.product_list, name="product_list"),
    path(
        "products/category/<slug:category_slug>/",
        views.product_list,
        name="product_list_by_category",
    ),
    path("products/<slug:slug>/", views.product_detail, name="product_detail"),
    path("wishlist/", views.wishlist_view, name="wishlist"),
    path("wishlist/toggle/<int:product_id>/", views.toggle_wishlist, name="toggle_wishlist"),
    path("about/", views.about_page, name="about"),
    path("contact/", views.contact_page, name="contact"),
    path("faq/", views.faq_page, name="faq"),
    path("blog/", views.blog_list, name="blog_list"),
    path("blog/<slug:slug>/", views.blog_detail, name="blog_detail"),
    path("collections/<slug:slug>/", views.collection_detail, name="collection_detail"),
    path("newsletter/subscribe/", views.newsletter_subscribe, name="newsletter_subscribe"),
    path("share/<int:product_id>/", views.product_share, name="product_share"),
    path("page/<slug:slug>/", views.page_detail, name="page_detail"),
    path("promo-banner/", TemplateView.as_view(template_name="pages/promo_banner.html"), name="promo_banner"),
    path("search/", views.product_list, name="search"),
    # API Endpoints
    path("api/share/<int:product_id>/", views.share_api, name="share_api"),
    path("api/share-all/", views.share_all_products_api, name="share_all_api"),
    path("api/recommendations/<int:product_id>/", views.recommendations_api, name="recommendations_api"),
    path("api/loyalty/", views.loyalty_points_api, name="loyalty_api"),
    path("api/sentiment/", views.sentiment_api, name="sentiment_api"),
    path("api/forecast/", views.forecast_api, name="forecast_api"),
    path("api/social-image/<int:product_id>/", views.social_image, name="social_image_default"),
    path("api/social-image/<int:product_id>/<str:platform>/", views.social_image, name="social_image"),
    # Tracking & Chatbot
    path("api/track/", track_engagement, name="track_engagement"),
    path("api/chatbot/", chatbot_api, name="chatbot_api"),
    path("api/cookie-consent/", cookie_consent_save, name="cookie_consent"),
    # GDPR
    path("api/my-data/", gdpr_data_export, name="gdpr_data_export"),
    path("api/my-data/csv/", gdpr_data_export_csv, name="gdpr_data_export_csv"),
    path("api/delete-account/", gdpr_delete_account, name="gdpr_delete_account"),
]
