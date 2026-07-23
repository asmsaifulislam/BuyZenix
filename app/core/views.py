import re
import io
import hashlib
from PIL import Image
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Sum, Count, Case, When, IntegerField, Avg
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.views.decorators.cache import cache_control

from core.models import Category, Product, Wishlist, Review, BlogPost, Collection, NewsletterSubscriber, ProductRedirect
from dashboard.models import Banner, Page


def home(request):
    categories = Category.objects.all()[:6]
    banners = Banner.objects.filter(is_active=True)[:5]
    from dashboard.models import Promotion
    hero_left = Promotion.objects.filter(is_active=True, position="hero_left").first()
    hero_right = Promotion.objects.filter(is_active=True, position="hero_right").first()

    price_sort = request.GET.get('sort_price')

    if price_sort == 'low_to_high':
        featured = Product.objects.filter(available=True, featured=True, is_archived=False).order_by('price')[:8]
        new_arrivals = Product.objects.filter(available=True, is_archived=False).order_by('price')[:8]
    elif price_sort == 'high_to_low':
        featured = Product.objects.filter(available=True, featured=True, is_archived=False).order_by('-price')[:8]
        new_arrivals = Product.objects.filter(available=True, is_archived=False).order_by('-price')[:8]
    else:
        featured = Product.objects.filter(available=True, featured=True, is_archived=False)[:8]
        new_arrivals = Product.objects.filter(available=True, is_archived=False)[:8]

    collections = Collection.objects.filter(is_active=True)[:4]

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
            "collections": collections,
        },
    )


def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True, is_archived=False)

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    query = request.GET.get("q")
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")
    if min_price:
        try:
            products = products.filter(price__gte=Decimal(min_price))
        except Exception:
            pass
    if max_price:
        try:
            products = products.filter(price__lte=Decimal(max_price))
        except Exception:
            pass

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

    paginator = Paginator(products, 20)
    page = request.GET.get("page")
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

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
            "min_price": min_price or "",
            "max_price": max_price or "",
        },
    )


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
    try:
        product = Product.objects.get(slug=slug, available=True, is_archived=False)
    except Product.DoesNotExist:
        redirect_obj = ProductRedirect.objects.filter(old_slug=slug).first()
        if redirect_obj:
            return redirect("core:product_detail", slug=redirect_obj.new_product.slug)
        raise
    gallery = product.gallery.all()
    colors = sorted(set(img.color for img in gallery if img.color))
    gallery_data = []
    for img in gallery:
        gallery_data.append({
            "url": img.image.url if img.image else "",
            "color": img.color or "",
            "size": img.size.name if img.size else "",
            "angle": img.angle or "",
            "label": img.label or "",
            "position": img.position,
        })

    stop_words = {"for", "the", "a", "an", "and", "or", "with", "in", "on", "at", "to", "of", "by", "is", "it", "from", "no", "not", "pro", "plus", "max", "new", "old"}
    words = [w for w in product.name.lower().split() if len(w) > 1 and w not in stop_words]

    q = Q()
    for w in words:
        q |= Q(name__icontains=w)
    conditions = [When(name__icontains=w, then=1) for w in words]
    related = (
        Product.objects.filter(q, available=True, is_archived=False)
        .exclude(id=product.id)
        .exclude(name__iexact=product.name)
        .annotate(
            match_count=Sum(Case(*conditions, default=0, output_field=IntegerField()))
        )
        .order_by("-match_count")[:4]
    )

    spec_lines, warranty_info = _parse_description(product.description)

    reviews = product.reviews.select_related("user").all()
    avg_rating = reviews.aggregate(avg=Avg("rating"))["avg"] or 0
    review_count = reviews.count()

    is_wishlisted = False
    if request.user.is_authenticated:
        is_wishlisted = Wishlist.objects.filter(user=request.user, product=product).exists()

    if request.method == "POST" and request.user.is_authenticated:
        if request.POST.get("review_submit"):
            rating = int(request.POST.get("rating", 5))
            title = request.POST.get("review_title", "").strip()
            body = request.POST.get("review_body", "").strip()
            Review.objects.update_or_create(
                user=request.user, product=product,
                defaults={"rating": rating, "title": title, "body": body}
            )
            return redirect("core:product_detail", slug=slug)

    social_img_base = request.build_absolute_uri("/").rstrip("/") + f"/api/social-image/{product.id}"

    return render(
        request,
        "core/product_detail.html",
        {"product": product, "related": related, "gallery": gallery,
         "colors": colors, "gallery_data": gallery_data,
         "spec_lines": spec_lines, "warranty_info": warranty_info,
         "reviews": reviews, "avg_rating": round(avg_rating, 1),
         "review_count": review_count, "is_wishlisted": is_wishlisted,
         "social_img_base": social_img_base},
    )


@login_required
@require_POST
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    obj, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if not created:
        obj.delete()
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"wishlisted": created})
    return redirect("core:product_detail", slug=product.slug)


@login_required
def wishlist_view(request):
    items = Wishlist.objects.filter(user=request.user).select_related("product", "product__category")
    return render(request, "core/wishlist.html", {"items": items})


def about_page(request):
    return render(request, "pages/about.html")


def contact_page(request):
    sent = False
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        message = request.POST.get("message", "").strip()
        if name and email and message:
            from django.core.mail import send_mail
            try:
                send_mail(
                    f"Contact from {name}",
                    f"From: {name} ({email})\n\n{message}",
                    email,
                    ["support@buyzenix.com"],
                    fail_silently=True,
                )
            except Exception:
                pass
            sent = True
    return render(request, "pages/contact.html", {"sent": sent})


def faq_page(request):
    return render(request, "pages/faq.html")


def blog_list(request):
    posts = BlogPost.objects.filter(is_published=True)[:20]
    return render(request, "core/blog_list.html", {"posts": posts})


def blog_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, is_published=True)
    return render(request, "core/blog_detail.html", {"post": post})


def collection_detail(request, slug):
    collection = get_object_or_404(Collection, slug=slug, is_active=True)
    products = collection.products.filter(available=True)
    return render(request, "core/collection_detail.html", {
        "collection": collection, "products": products,
    })


@require_POST
def newsletter_subscribe(request):
    email = request.POST.get("email", "").strip()
    if email:
        NewsletterSubscriber.objects.get_or_create(email=email)
    return redirect(request.META.get("HTTP_REFERER") or "core:home")


def page_detail(request, slug):
    page = get_object_or_404(Page, slug=slug, is_published=True)
    return render(request, "core/page_detail.html", {"page": page})


def product_share(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product_url = request.build_absolute_uri(f"/products/{product.slug}/")
    social = get_social_share_urls(request, product)
    share_urls = {k: v["share"] for k, v in social.items()}
    return render(request, "core/product_share.html", {
        "product": product,
        "product_url": product_url,
        "share_urls": share_urls,
        "social": social,
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
    products = Product.objects.filter(available=True, is_archived=False)[:50]
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
    from dashboard.models import ProductRecommendation
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


SOCIAL_IMAGE_SIZES = {
    "facebook":   (1200, 630),
    "instagram":  (1080, 1080),
    "instagram_story": (1080, 1920),
    "tiktok":     (1080, 1920),
    "twitter":    (1200, 675),
    "linkedin":   (1200, 627),
    "pinterest":  (1000, 1500),
    "whatsapp":   (1200, 630),
}


@cache_control(max_age=86400)
def social_image(request, product_id, platform="facebook"):
    product = get_object_or_404(Product, id=product_id)
    if not product.image:
        return HttpResponse(status=404)

    target_w, target_h = SOCIAL_IMAGE_SIZES.get(platform, (1200, 630))
    target_ratio = target_w / target_h

    try:
        img = Image.open(product.image.path)
        img = img.convert("RGB")
    except Exception:
        return HttpResponse(status=404)

    src_w, src_h = img.size
    src_ratio = src_w / src_h

    if src_ratio > target_ratio:
        new_h = src_h
        new_w = int(src_h * target_ratio)
    else:
        new_w = src_w
        new_h = int(src_w / target_ratio)

    left = (src_w - new_w) // 2
    top = (src_h - new_h) // 2
    img = img.crop((left, top, left + new_w, top + new_h))
    img = img.resize((target_w, target_h), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90, optimize=True)
    buf.seek(0)

    response = HttpResponse(buf.getvalue(), content_type="image/jpeg")
    etag = hashlib.md5(f"{product_id}-{platform}-{product.image.name}".encode()).hexdigest()
    response["ETag"] = etag
    response["Cache-Control"] = "public, max-age=86400"
    response["Content-Length"] = len(buf.getvalue())
    response["Vary"] = "Accept"
    return response


def get_social_image_url(request, product_id, platform="facebook"):
    return request.build_absolute_uri(f"/api/social-image/{product_id}/{platform}/")


def get_social_share_urls(request, product):
    base = request.build_absolute_uri("/").rstrip("/")
    product_url = f"{base}/products/{product.slug}/"
    image_base = f"{base}/api/social-image/{product.id}"

    platforms = {
        "facebook": {
            "share": f"https://www.facebook.com/sharer/sharer.php?u={product_url}",
            "image": f"{image_base}/facebook/",
            "size": "1200x630",
        },
        "instagram": {
            "share": "https://www.instagram.com/",
            "image": f"{image_base}/instagram/",
            "size": "1080x1080",
        },
        "tiktok": {
            "share": "https://www.tiktok.com/",
            "image": f"{image_base}/tiktok/",
            "size": "1080x1920",
        },
        "twitter": {
            "share": f"https://twitter.com/intent/tweet?url={product_url}&text={product.name}",
            "image": f"{image_base}/twitter/",
            "size": "1200x675",
        },
        "linkedin": {
            "share": f"https://www.linkedin.com/sharing/share-offsite/?url={product_url}",
            "image": f"{image_base}/linkedin/",
            "size": "1200x627",
        },
        "whatsapp": {
            "share": f"https://wa.me/?text={product.name}%20{product_url}",
            "image": f"{image_base}/whatsapp/",
            "size": "1200x630",
        },
        "telegram": {
            "share": f"https://t.me/share/url?url={product_url}&text={product.name}",
            "image": f"{image_base}/facebook/",
            "size": "1200x630",
        },
        "pinterest": {
            "share": f"https://pinterest.com/pin/create/button/?url={product_url}&description={product.name}",
            "image": f"{image_base}/pinterest/",
            "size": "1000x1500",
        },
    }
    return platforms
