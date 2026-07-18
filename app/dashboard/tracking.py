import threading
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin


class PageViewTracker(MiddlewareMixin):
    """Track page views asynchronously without slowing down responses."""

    def process_response(self, request, response):
        if request.method != "GET":
            return response
        if response.status_code != 200:
            return response
        if request.path.startswith("/admin/") or request.path.startswith("/static/") or request.path.startswith("/media/"):
            return response

        def _save():
            try:
                from dashboard.models import PageView
                from core.models import Product

                product = None
                if request.resolver_match and request.resolver_match.url_name == "product_detail":
                    slug = request.resolver_match.kwargs.get("slug", "")
                    try:
                        product = Product.objects.get(slug=slug)
                    except Product.DoesNotExist:
                        pass

                PageView.objects.create(
                    url=request.path,
                    product=product,
                    user=request.user if request.user.is_authenticated else None,
                    ip_address=_anonymize_ip(request),
                    user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
                    referrer=request.META.get("HTTP_REFERER", "")[:500],
                    session_key=request.session.session_key or "",
                )
            except Exception:
                pass

        thread = threading.Thread(target=_save, daemon=True)
        thread.start()
        return response


def _anonymize_ip(request):
    """Anonymize IP address for GDPR compliance."""
    ip = _get_client_ip(request)
    if not ip:
        return None

    anonymize = getattr(settings, "GDPR_ANONYMIZE_IP", True)
    if anonymize and ip:
        if ":" in ip:
            # IPv6: zero last 80 bits
            parts = ip.split(":")
            return ":".join(parts[:5] + ["0"] * 3)
        else:
            # IPv4: zero last octet
            parts = ip.split(".")
            if len(parts) == 4:
                return ".".join(parts[:3] + ["0"])
    return ip


def _get_client_ip(request):
    x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded:
        return x_forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
