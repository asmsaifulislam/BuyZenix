import json
import csv
from io import StringIO, BytesIO
from datetime import timedelta

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Sum, Q, F
from django.db.models.functions import TruncDate
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone


@staff_member_required
def report_revenue(request):
    """Export revenue report as CSV."""
    days = int(request.GET.get("days", 30))
    since = timezone.now() - timedelta(days=days)

    from orders.models import Order
    orders = Order.objects.filter(created__gte=since).order_by("created")

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Order ID", "Date", "Customer", "Status", "Total"])

    for order in orders:
        writer.writerow([
            order.id,
            order.created.strftime("%Y-%m-%d %H:%M"),
            order.user.username if order.user else "Guest",
            order.status,
            str(order.get_total_cost()),
        ])

    response = HttpResponse(output.getvalue(), content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="revenue_report_{days}d.csv"'
    return response


@staff_member_required
def report_products(request):
    """Export product performance report as CSV."""
    from core.models import Product
    from orders.models import OrderItem
    from dashboard.models import PageView

    products = Product.objects.annotate(
        total_sold=Count("orderitem"),
        total_revenue=Sum("orderitem__price"),
        total_views=Count("page_views"),
    ).order_by("-total_revenue")

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Product", "Category", "Price", "Stock", "Sold", "Revenue (BDT)", "Views", "Conversion %"])

    for p in products:
        conversion = 0
        if p.total_views > 0:
            conversion = round((p.total_sold / p.total_views) * 100, 2)
        writer.writerow([
            p.name,
            p.category.name if p.category else "Uncategorized",
            str(p.price),
            p.stock,
            p.total_sold or 0,
            str(p.total_revenue or 0),
            p.total_views or 0,
            conversion,
        ])

    response = HttpResponse(output.getvalue(), content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="product_report.csv"'
    return response


@staff_member_required
def report_users(request):
    """Export user activity report as CSV."""
    from orders.models import Order
    from dashboard.models import UserActivity, LoyaltyPoint
    from django.contrib.auth.models import User

    users = User.objects.annotate(
        order_count=Count("order"),
        total_spent=Sum("order__items__price"),
    ).order_by("-order_count")

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Username", "Email", "Date Joined", "Orders", "Total Spent", "Loyalty Points", "Activities"])

    for u in users:
        points = LoyaltyPoint.get_balance(u)
        activities = UserActivity.objects.filter(user=u).count()
        writer.writerow([
            u.username,
            u.email,
            u.date_joined.strftime("%Y-%m-%d"),
            u.order_count,
            str(u.total_spent or 0),
            points,
            activities,
        ])

    response = HttpResponse(output.getvalue(), content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="user_report.csv"'
    return response


@staff_member_required
def report_plotly_chart(request):
    """Render interactive Plotly charts for BI dashboard."""
    days = int(request.GET.get("days", 30))
    since = timezone.now() - timedelta(days=days)

    from orders.models import Order
    daily = (
        Order.objects.filter(created__gte=since)
        .annotate(date=TruncDate("created"))
        .values("date")
        .annotate(revenue=Sum("items__price"), count=Count("id"))
        .order_by("date")
    )

    dates = [d["date"].strftime("%b %d") for d in daily]
    revenues = [float(d["revenue"] or 0) for d in daily]
    order_counts = [d["count"] for d in daily]

    try:
        import plotly.graph_objects as go
        from plotly.offline import plot

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates, y=revenues, mode="lines+markers", name="Revenue (BDT)", line=dict(color="#6366f1", width=3)))
        fig.add_trace(go.Bar(x=dates, y=order_counts, name="Orders", yaxis="y2", marker_color="#a78bfa"))
        fig.update_layout(
            title=f"Revenue & Orders — Last {days} Days",
            xaxis_title="Date",
            yaxis_title="Revenue (BDT)",
            yaxis2=dict(title="Orders", overlaying="y", side="right"),
            template="plotly_white",
            height=450,
        )
        chart_html = plot(fig, output_type="div", include_plotlyjs="cdn")
    except ImportError:
        chart_html = '<p style="color:#94a3b8">Install plotly: <code>pip install plotly</code></p>'

    return render(request, "dashboard/admin_plotly.html", {"chart_html": chart_html, "days": days})
