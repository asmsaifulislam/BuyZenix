from django.conf import settings
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from core.models import Category, Product
from dashboard.models import Banner, Page


def home(request):
    categories = Category.objects.all()[:6]
    banners = Banner.objects.filter(is_active=True)[:5]
    from dashboard.models import Promotion
    hero_left = Promotion.objects.filter(is_active=True, position="hero_left").first()
    hero_right = Promotion.objects.filter(is_active=True, position="hero_right").first()
    
    # Handle price filter - sort products by price
    price_sort = request.GET.get('sort_price')
    
    if price_sort == 'low_to_high':
        featured = Product.objects.filter(available=True, featured=True).order_by('price')[:8]
        new_arrivals = Product.objects.filter(available=True).order_by('price')[:8]
    elif price_sort == 'high_to_low':
        featured = Product.objects.filter(available=True, featured=True).order_by('-price')[:8]
        new_arrivals = Product.objects.filter(available=True).order_by('-price')[:8]
    else:
        featured = Product.objects.filter(available=True, featured=True)[:8]
        new_arrivals = Product.objects.filter(available=True)[:8]
    
    return render(
        request,
        "core/home.html",
        {
            "featured": featured,
            "categories": categories,
            "new_arrivals": new_arrivals,
            "banners": banners,
            "hero_left": hero_left,
            "hero_right": hero_right,
            "price_sort": price_sort,
        },
    )


def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    query = request.GET.get("q")
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    sort_price = request.GET.get("sort_price")
    sort_date = request.GET.get("sort_date")

    if sort_price == "low_to_high":
        products = products.order_by("price")
    elif sort_price == "high_to_low":
        products = products.order_by("-price")

    if sort_date == "newest":
        products = products.order_by("-created")
    elif sort_date == "oldest":
        products = products.order_by("created")

    return render(
        request,
        "core/product_list.html",
        {
            "category": category,
            "categories": categories,
            "products": products,
            "query": query,
            "sort_price": sort_price,
            "sort_date": sort_date,
        },
    )


import re


def _parse_description(text):
    spec_lines = []
    warranty_info = ""
    if not text:
        return spec_lines, warranty_info

    warranty_keywords = ["warranty", "guarantee", "replacement"]
    raw_lines = [l.strip() for l in re.split(r'[\n\r]+', text) if l.strip()]

    for line in raw_lines:
        low = line.lower()
        if any(kw in low for kw in warranty_keywords):
            warranty_info = line
            continue
        m = re.match(r'^([^:]+):\s*(.+)$', line)
        if m:
            spec_lines.append({"key": m.group(1).strip(), "value": m.group(2).strip()})
        else:
            spec_lines.append({"key": "Details", "value": line})

    return spec_lines, warranty_info


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, available=True)
    gallery = product.gallery.all()
    related = Product.objects.filter(category=product.category, available=True).exclude(
        id=product.id
    )[:4]
    spec_lines, warranty_info = _parse_description(product.description)
    return render(
        request,
        "core/product_detail.html",
        {"product": product, "related": related, "gallery": gallery,
         "spec_lines": spec_lines, "warranty_info": warranty_info},
    )


def page_detail(request, slug):
    page = get_object_or_404(Page, slug=slug, is_published=True)
    return render(request, "core/page_detail.html", {"page": page})


def product_share(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product_url = request.build_absolute_uri(f"/products/{product.slug}/")
    share_urls = {
        "facebook": f"https://www.facebook.com/sharer/sharer.php?u={product_url}",
        "twitter": f"https://twitter.com/intent/tweet?url={product_url}&text={product.name}",
        "whatsapp": f"https://wa.me/?text={product.name}%20{product_url}",
        "linkedin": f"https://www.linkedin.com/sharing/share-offsite/?url={product_url}",
        "telegram": f"https://t.me/share/url?url={product_url}&text={product.name}",
        "tiktok": f"https://www.tiktok.com/",
        "instagram": f"https://www.instagram.com/",
    }
    return render(request, "core/product_share.html", {
        "product": product,
        "product_url": product_url,
        "share_urls": share_urls,
    })


def share_api(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    base_url = request.build_absolute_uri("/").rstrip("/")
    product_url = f"{base_url}/products/{product.slug}/"
    image_url = ""
    if product.image:
        image_url = request.build_absolute_uri(product.image.url)
    return JsonResponse({
        "product": {
            "id": product.id,
            "name": product.name,
            "price": str(product.price),
            "url": product_url,
            "image": image_url,
            "description": product.description[:300] if product.description else "",
        },
        "share_urls": {
            "facebook": f"https://www.facebook.com/sharer/sharer.php?u={product_url}",
            "twitter": f"https://twitter.com/intent/tweet?url={product_url}&text={product.name}",
            "whatsapp": f"https://wa.me/?text={product.name}%20{product_url}",
            "linkedin": f"https://www.linkedin.com/sharing/share-offsite/?url={product_url}",
            "telegram": f"https://t.me/share/url?url={product_url}&text={product.name}",
            "tiktok": f"https://www.tiktok.com/",
            "instagram": f"https://www.instagram.com/",
        },
        "copy_url": product_url,
    })


def share_all_products_api(request):
    products = Product.objects.filter(available=True)[:50]
    base_url = request.build_absolute_uri("/").rstrip("/")
    data = []
    for p in products:
        product_url = f"{base_url}/products/{p.slug}/"
        data.append({
            "id": p.id,
            "name": p.name,
            "price": str(p.price),
            "url": product_url,
            "share_urls": {
                "facebook": f"https://www.facebook.com/sharer/sharer.php?u={product_url}",
                "twitter": f"https://twitter.com/intent/tweet?url={product_url}&text={p.name}",
                "whatsapp": f"https://wa.me/?text={p.name}%20{product_url}",
                "linkedin": f"https://www.linkedin.com/sharing/share-offsite/?url={product_url}",
                "telegram": f"https://t.me/share/url?url={product_url}&text={p.name}",
                "tiktok": f"https://www.tiktok.com/",
                "instagram": f"https://www.instagram.com/",
            },
        })
    return JsonResponse({"products": data, "count": len(data)})


def recommendations_api(request, product_id):
    from dashboard.models import UserActivity, ProductRecommendation
    from django.db.models import Count
    product = get_object_or_404(Product, id=product_id)

    manual = ProductRecommendation.objects.filter(
        source_product=product
    ).select_related("recommended_product")[:8]

    if manual.exists():
        recs = [
            {
                "id": r.recommended_product.id,
                "name": r.recommended_product.name,
                "price": str(r.recommended_product.price),
                "score": r.score,
            }
            for r in manual
        ]
    else:
        same_cat = Product.objects.filter(
            category=product.category, available=True
        ).exclude(id=product.id).order_by("-created")[:8]
        recs = [
            {
                "id": p.id,
                "name": p.name,
                "price": str(p.price),
                "score": 0.5,
            }
            for p in same_cat
        ]

    return JsonResponse({
        "product_id": product.id,
        "recommendations": recs,
    })


def set_currency(request):
    code = (request.GET.get("code") or "").upper()
    if code in settings.CURRENCIES:
        request.session["currency"] = code
    return redirect(request.GET.get("next") or request.META.get("HTTP_REFERER") or "core:home")


def loyalty_points_api(request):
    from dashboard.models import LoyaltyPoint
    from django.contrib.auth.models import User
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Login required"}, status=401)
    balance = LoyaltyPoint.get_balance(request.user)
    history = LoyaltyPoint.objects.filter(user=request.user)[:20]
    return JsonResponse({
        "user": request.user.username,
        "balance": balance,
        "history": [
            {"points": h.points, "reason": h.reason, "date": h.created.isoformat()}
            for h in history
        ],
    })


def sentiment_api(request):
    from orders.models import Order
    from django.db.models import Count, Q
    total = Order.objects.count()
    delivered = Order.objects.filter(status="delivered").count()
    cancelled = Order.objects.filter(status="cancelled").count()
    good_rate = (delivered / total * 100) if total else 0
    bad_rate = (cancelled / total * 100) if total else 0
    return JsonResponse({
        "total_orders": total,
        "delivered": delivered,
        "cancelled": cancelled,
        "good_rate": round(good_rate, 1),
        "bad_rate": round(bad_rate, 1),
        "sentiment": "positive" if good_rate > 60 else "neutral" if good_rate > 40 else "negative",
    })


def forecast_api(request):
    from orders.models import Order, OrderItem
    from core.models import Product
    from django.db.models import Sum, Count
    from django.utils import timezone
    from datetime import timedelta

    now = timezone.now()
    last_30 = now - timedelta(days=30)
    prev_30 = last_30 - timedelta(days=30)

    current_orders = Order.objects.filter(created__gte=last_30).count()
    prev_orders = Order.objects.filter(created__gte=prev_30, created__lt=last_30).count()

    growth = ((current_orders - prev_orders) / prev_orders * 100) if prev_orders else 0

    trending = (
        OrderItem.objects.filter(order__created__gte=last_30)
        .values("product__name", "product__id")
        .annotate(total=Count("id"), revenue=Sum("price"))
        .order_by("-total")[:10]
    )

    return JsonResponse({
        "current_month_orders": current_orders,
        "previous_month_orders": prev_orders,
        "growth_percent": round(growth, 1),
        "trending_products": [
            {"id": t["product__id"], "name": t["product__name"], "orders": t["total"], "revenue": float(t["revenue"] or 0)}
            for t in trending
        ],
        "prediction": "Growing" if growth > 10 else "Stable" if growth > -10 else "Declining",
    })
