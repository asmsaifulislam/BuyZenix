import threading
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin


class AuditLogMiddleware(MiddlewareMixin):
    """Log important actions (orders, logins) asynchronously."""

    def process_response(self, request, response):
        if response.status_code not in (200, 302):
            return response

        def _save():
            try:
                from dashboard.models import AuditLog

                action = None
                model_name = ""
                object_repr = ""
                details = {}

                if request.resolver_match:
                    url_name = request.resolver_match.url_name or ""

                    if url_name == "order_complete" and request.method == "GET":
                        order_id = request.resolver_match.kwargs.get("order_id")
                        action = "order"
                        model_name = "Order"
                        object_id = str(order_id)
                        object_repr = f"Order #{order_id}"
                        details = {"user": str(request.user)}

                    elif url_name == "login" and request.method == "POST" and response.status_code == 302:
                        action = "login"
                        model_name = "User"
                        object_repr = str(request.user)

                    if action:
                        AuditLog.objects.create(
                            user=request.user if request.user.is_authenticated else None,
                            action=action,
                            model_name=model_name,
                            object_id=object_id if action == "order" else "",
                            object_repr=object_repr,
                            details=details,
                            ip_address=_anonymize_ip(request),
                        )
            except Exception:
                pass

        thread = threading.Thread(target=_save, daemon=True)
        thread.start()
        return response


def _anonymize_ip(request):
    ip = _get_ip(request)
    if not ip:
        return None
    anonymize = getattr(settings, "GDPR_ANONYMIZE_IP", True)
    if anonymize and ip:
        if ":" in ip:
            parts = ip.split(":")
            return ":".join(parts[:5] + ["0"] * 3)
        else:
            parts = ip.split(".")
            if len(parts) == 4:
                return ".".join(parts[:3] + ["0"])
    return ip


def _get_ip(request):
    x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded:
        return x_forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
