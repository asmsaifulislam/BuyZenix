import json
import csv
from io import StringIO

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from datetime import timedelta


@login_required
def gdpr_data_export(request):
    """Export all user data as JSON (GDPR right to data portability)."""
    user = request.user
    profile = getattr(user, "profile", None)

    data = {
        "export_date": timezone.now().isoformat(),
        "user": {
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "date_joined": user.date_joined.isoformat(),
        },
        "profile": {
            "role": profile.role if profile else "customer",
            "company_name": profile.company_name if profile else "",
            "phone": profile.phone if profile else "",
            "address": profile.address_line1 if profile else "",
            "city": profile.city if profile else "",
            "state": profile.state if profile else "",
            "country": profile.country if profile else "",
        } if profile else None,
        "orders": [],
        "page_views": [],
        "loyalty_points": [],
        "activities": [],
    }

    from orders.models import Order
    for order in Order.objects.filter(user=user).select_related("items__product"):
        data["orders"].append({
            "id": order.id,
            "status": order.status,
            "total": str(order.get_total_cost()),
            "created": order.created.isoformat(),
            "items": [{"product": item.product.name, "qty": item.quantity, "price": str(item.price)} for item in order.items.all()],
        })

    from dashboard.models import PageView
    for pv in PageView.objects.filter(user=user)[:500]:
        data["page_views"].append({
            "url": pv.url,
            "viewed_at": pv.viewed_at.isoformat(),
        })

    from dashboard.models import LoyaltyPoint
    for lp in LoyaltyPoint.objects.filter(user=user):
        data["loyalty_points"].append({
            "points": lp.points,
            "reason": lp.reason,
            "created": lp.created.isoformat(),
        })

    from dashboard.models import UserActivity
    for ua in UserActivity.objects.filter(user=user):
        data["activities"].append({
            "type": ua.activity_type,
            "product": ua.product.name if ua.product else None,
            "created": ua.created.isoformat(),
        })

    response = HttpResponse(
        json.dumps(data, indent=2, default=str),
        content_type="application/json",
    )
    response["Content-Disposition"] = f'attachment; filename="buyzenix_data_{user.username}.json"'
    return response


@login_required
def gdpr_data_export_csv(request):
    """Export user orders as CSV."""
    user = request.user
    from orders.models import Order, OrderItem

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Order ID", "Date", "Status", "Product", "Quantity", "Price", "Total"])

    for order in Order.objects.filter(user=user):
        items = OrderItem.objects.filter(order=order).select_related("product")
        for item in items:
            writer.writerow([
                order.id,
                order.created.strftime("%Y-%m-%d"),
                order.status,
                item.product.name,
                item.quantity,
                str(item.price),
                str(order.get_total_cost()),
            ])

    response = HttpResponse(output.getvalue(), content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="buyzenix_orders_{user.username}.csv"'
    return response


@login_required
def gdpr_delete_account(request):
    """Right to deletion — delete user account and all data."""
    if request.method != "POST":
        return redirect("accounts:dashboard")

    user = request.user
    username = user.username

    from orders.models import Order, OrderItem
    from dashboard.models import PageView, AuditLog, LoyaltyPoint, UserActivity

    Order.objects.filter(user=user).delete()
    PageView.objects.filter(user=user).delete()
    LoyaltyPoint.objects.filter(user=user).delete()
    UserActivity.objects.filter(user=user).delete()
    AuditLog.objects.filter(user=user).delete()

    if hasattr(user, "profile"):
        user.profile.delete()

    user.delete()
    messages.success(request, f"Account '{username}' and all data have been permanently deleted.")
    return redirect("core:home")


def cookie_consent_save(request):
    """Save cookie consent preferences via AJAX."""
    if request.method != "POST":
        return JsonResponse({"ok": False}, status=405)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"ok": False}, status=400)

    consent = {
        "necessary": True,
        "analytics": data.get("analytics", False),
        "marketing": data.get("marketing", False),
        "preferences": data.get("preferences", False),
        "timestamp": timezone.now().isoformat(),
    }

    response = JsonResponse({"ok": True})
    response.set_cookie(
        "gdpr_consent",
        json.dumps(consent),
        max_age=365 * 24 * 60 * 60,
        httponly=False,
        samesite="Lax",
    )
    return response


def privacy_policy(request):
    """Render privacy policy page."""
    return render(request, "pages/privacy_policy.html")
