import json
from django.conf import settings


def analytics_context(request):
    """Inject analytics/tracking config into all templates."""
    ctx = {
        "google_analytics_id": "",
        "matomo_url": "",
        "matomo_site_id": "",
        "smartlook_key": "",
        "gdpr_consent_required": getattr(settings, "GDPR_COOKIE_CONSENT_REQUIRED", True),
        "gdpr_anonymize_ip": getattr(settings, "GDPR_ANONYMIZE_IP", True),
        "gdpr_contact_email": getattr(settings, "GDPR_CONTACT_EMAIL", ""),
        "gdpr_dpo_email": getattr(settings, "GDPR_DPO_EMAIL", ""),
    }

    # Check user consent from cookie
    consent_cookie = request.COOKIES.get("gdpr_consent", "")
    if consent_cookie:
        try:
            consent = json.loads(consent_cookie)
            ctx["user_consent"] = consent
        except (json.JSONDecodeError, ValueError):
            ctx["user_consent"] = {}
    else:
        ctx["user_consent"] = {}

    # Load active API keys for analytics
    try:
        from dashboard.models import APIKey
        for api in APIKey.objects.filter(is_active=True, category="tracking"):
            name_lower = api.name.lower()
            if "google" in name_lower or "ga" in name_lower or "gtag" in name_lower:
                ctx["google_analytics_id"] = api.api_key
            elif "matomo" in name_lower or "piwik" in name_lower:
                ctx["matomo_url"] = api.endpoint or api.api_key
                ctx["matomo_site_id"] = api.api_secret
            elif "smartlook" in name_lower:
                ctx["smartlook_key"] = api.api_key
    except Exception:
        pass

    return ctx
