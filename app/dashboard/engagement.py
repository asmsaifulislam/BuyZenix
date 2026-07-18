import json
import threading
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required


@csrf_exempt
@require_POST
def track_engagement(request):
    """Log frontend click/engagement events."""
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"ok": False}, status=400)

    event_type = data.get("event", "")
    product_id = data.get("product_id")
    url = data.get("url", "")
    meta = data.get("meta", {})

    def _save():
        try:
            from dashboard.models import UserActivity

            user = request.user if request.user.is_authenticated else None
            product = None
            if product_id:
                from core.models import Product
                try:
                    product = Product.objects.get(pk=product_id)
                except Product.DoesNotExist:
                    pass

            activity_type = "view"
            if event_type in ("add_to_cart", "cart_add"):
                activity_type = "cart"
            elif event_type in ("purchase", "order_complete"):
                activity_type = "purchase"
            elif event_type in ("share", "share_click"):
                activity_type = "share"
            elif event_type in ("review",):
                activity_type = "review"

            if user:
                UserActivity.objects.create(
                    user=user,
                    product=product,
                    activity_type=activity_type,
                )
        except Exception:
            pass

    thread = threading.Thread(target=_save, daemon=True)
    thread.start()
    return JsonResponse({"ok": True})
