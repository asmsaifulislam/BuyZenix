import json
import re

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db.models import Q, Avg, Min, Max, Count


# ─── Intent detection ───

def _detect_intent(msg):
    """Classify user message into an intent."""
    m = msg.lower().strip()

    if re.search(r'\b(hi|hello|hey|assalam|namaste|good\s*(morning|afternoon|evening)|yo|sup)\b', m):
        return "greeting"
    if re.search(r'\b(thank|thanks|shukriya|tq)\b', m):
        return "thanks"
    if re.search(r'\b(bye|goodbye|alvida|see\s*you)\b', m):
        return "bye"
    if re.search(r'\b(help|what\s*can|options|menu)\b', m):
        return "help"

    if re.search(r'\b(product|item|sell|available|stock|what\s*(do|have|is)|catalog|shop|browse)\b', m):
        return "products"
    if re.search(r'\b(categor|cat|type|group|section)\b', m):
        return "categories"
    if re.search(r'\b(price|cost|how\s*much|taka|bdt|৳|\$|expensive|cheap|afford|budget)\b', m):
        return "price"
    if re.search(r'\b(feature|popular|best|top|recommend|suggest|new|latest|trending)\b', m):
        return "featured"
    if re.search(r'\b(sale|discount|offer|promo|coupon|code|off|deal)\b', m):
        return "coupons"
    if re.search(r'\b(order|my\s*order|track|where|status|delivery|shipped)\b', m):
        return "orders"
    if re.search(r'\b(return|refund|exchange|money\s*back)\b', m):
        return "returns"
    if re.search(r'\b(ship|delivery|deliver|delivering|courier|parcels?|when\s*(will|do))\b', m):
        return "shipping"
    if re.search(r'\b(pay|payment|bkash|nagad|card|cod|cash|visa|mastercard)\b', m):
        return "payments"
    if re.search(r'\b(account|login|register|sign\s*in|password|profile|signup)\b', m):
        return "account"
    if re.search(r'\b(contact|phone|email|support|help\s*desk|reach|call)\b', m):
        return "contact"
    if re.search(r'\b(warranty|guarantee|defect|broken|quality)\b', m):
        return "warranty"
    if re.search(r'\b(who|about|what\s*is\s*buyzenix|tell\s*me\s*about|company)\b', m):
        return "about"
    if re.search(r'\b(operating|open|hour|time|available|什么时候|什么时候)\b', m):
        return "hours"

    return "unknown"


# ─── Dynamic reply generators ───

def _reply_greeting():
    from dashboard.models import SiteSettings
    try:
        s = SiteSettings.objects.first()
        name = s.site_name if s else "BuyZenix"
    except Exception:
        name = "BuyZenix"
    return f"Hello! Welcome to {name}. I can help with products, orders, payments, shipping & more. What are you looking for?"


def _reply_help():
    return (
        "I can help with:\n"
        "• <strong>Products</strong> — ask what we sell, stock, prices\n"
        "• <strong>Categories</strong> — browse Electronics, Fashion, Home, Accessories\n"
        "• <strong>Prices</strong> — ask about any product price\n"
        "• <strong>Featured</strong> — see top/trending products\n"
        "• <strong>Coupons</strong> — check active discounts\n"
        "• <strong>Orders</strong> — track your orders\n"
        "• <strong>Shipping</strong> — delivery times & info\n"
        "• <strong>Payments</strong> — bKash, Nagad, COD, cards\n"
        "• <strong>Returns</strong> — return & refund policy\n"
        "• <strong>Contact</strong> — reach our support team"
    )


def _reply_products(msg):
    from core.models import Product, Category

    m = msg.lower().strip()

    # Check for category filter
    cats = Category.objects.all()
    cat_filter = None
    for c in cats:
        if c.name.lower() in m:
            cat_filter = c
            break

    # Check for keyword search
    search_q = Q()
    words = [w for w in re.findall(r'\b\w+\b', m) if len(w) > 2]
    skip = {'product', 'item', 'sell', 'available', 'stock', 'what', 'do', 'have',
            'is', 'catalog', 'shop', 'browse', 'tell', 'show', 'give', 'give',
            'about', 'your', 'the', 'some', 'any', 'all', 'with', 'for', 'and'}
    keywords = [w for w in words if w not in skip]
    if keywords:
        for kw in keywords:
            search_q |= Q(name__icontains=kw) | Q(description__icontains=kw)

    qs = Product.objects.filter(available=True)
    if cat_filter:
        qs = qs.filter(category=cat_filter)
    if search_q:
        qs = qs.filter(search_q)

    products = qs[:8]
    if not products:
        # Show all available
        products = Product.objects.filter(available=True)[:8]

    if not products:
        return "No products available right now. Check back soon!"

    lines = [f"📦 <strong>{products.count()} products found" + (f" in {cat_filter.name}" if cat_filter else "") + ":</strong>"]
    for p in products:
        price = f"৳{p.price}"
        if p.sale_price and p.sale_price < p.price:
            price = f"<s>৳{p.price}</s> → <strong>৳{p.sale_price}</strong> ⭐"
        stock_info = f"({p.stock} in stock)" if p.stock > 0 else "<em>out of stock</em>"
        lines.append(f"• <a href=\"{p.get_absolute_url()}\" style=\"color:#4f46e5\">{p.name}</a> — {price} {stock_info}")

    lines.append(f"\nBrowse all: <a href=\"/products/\" style=\"color:#4f46e5\">View Catalog →</a>")
    return "\n".join(lines)


def _reply_categories():
    from core.models import Category

    cats = Category.objects.annotate(cnt=Count('products')).filter(cnt__gt=0)
    if not cats:
        cats = Category.objects.all()

    if not cats:
        return "No categories yet. Products coming soon!"

    lines = ["📂 <strong>Our Categories:</strong>"]
    for c in cats:
        cnt = c.products.filter(available=True).count() if hasattr(c, 'cnt') else c.products.count()
        lines.append(f"• <a href=\"{c.get_absolute_url()}\" style=\"color:#4f46e5\">{c.name}</a> — {cnt} products")
    return "\n".join(lines)


def _reply_price(msg):
    from core.models import Product

    words = [w for w in re.findall(r'\b\w+\b', msg.lower()) if len(w) > 2]
    skip = {'price', 'cost', 'how', 'much', 'taka', 'bdt', 'expensive', 'cheap', 'afford', 'budget', 'the', 'what', 'is', 'of', 'for'}
    keywords = [w for w in words if w not in skip]

    qs = Product.objects.filter(available=True)
    if keywords:
        q = Q()
        for kw in keywords:
            q |= Q(name__icontains=kw)
        qs = qs.filter(q)

    products = qs[:5]
    if not products:
        # Price overview
        stats = Product.objects.filter(available=True).aggregate(
            min_price=Min('price'), max_price=Max('price'), avg_price=Avg('price')
        )
        if stats['min_price']:
            return (
                f"💰 <strong>Price Range:</strong><br>"
                f"Lowest: ৳{stats['min_price']}<br>"
                f"Highest: ৳{stats['max_price']}<br>"
                f"Average: ৳{int(stats['avg_price'])}<br><br>"
                f"Browse: <a href=\"/products/?sort_price=low_to_high\" style=\"color:#4f46e5\">Low → High</a> | "
                f"<a href=\"/products/?sort_price=high_to_low\" style=\"color:#4f46e5\">High → Low</a>"
            )
        return "No products available yet to check prices."

    lines = ["💰 <strong>Price Info:</strong>"]
    for p in products:
        price = f"৳{p.price}"
        if p.sale_price and p.sale_price < p.price:
            discount = int((1 - p.sale_price / p.price) * 100)
            price = f"~~৳{p.price}~~ → <strong>৳{p.sale_price}</strong> ({discount}% off!)"
        lines.append(f"• {p.name}: {price}")
    return "\n".join(lines)


def _reply_featured():
    from core.models import Product

    featured = Product.objects.filter(available=True, featured=True)[:5]
    latest = Product.objects.filter(available=True).order_by('-created')[:5]

    lines = ["⭐ <strong>Featured Products:</strong>"]
    if featured:
        for p in featured:
            price = f"৳{p.price}"
            if p.sale_price and p.sale_price < p.price:
                price = f"<s>৳{p.price}</s> → <strong>৳{p.sale_price}</strong>"
            lines.append(f"• <a href=\"{p.get_absolute_url()}\" style=\"color:#4f46e5\">{p.name}</a> — {price}")
    else:
        lines.append("No featured products right now.")

    if latest:
        lines.append("\n🆕 <strong>Latest Arrivals:</strong>")
        for p in latest:
            lines.append(f"• <a href=\"{p.get_absolute_url()}\" style=\"color:#4f46e5\">{p.name}</a> — ৳{p.price}")

    return "\n".join(lines)


def _reply_coupons():
    from dashboard.models import Coupon
    from django.utils import timezone

    now = timezone.now()
    active = Coupon.objects.filter(
        is_active=True,
        Q(valid_from__lte=now) | Q(valid_from__isnull=True),
        Q(valid_to__gte=now) | Q(valid_to__isnull=True),
    )
    active = [c for c in active if c.max_uses == 0 or c.used_count < c.max_uses]

    if not active:
        return "🏷️ No active coupons right now. Check our homepage for current promotions!"

    lines = ["🏷️ <strong>Active Coupons:</strong>"]
    for c in active[:5]:
        disc = f"{c.discount_value}%" if c.discount_type == 'percent' else f"৳{c.discount_value}"
        min_info = f" (min order: ৳{c.min_order_amount})" if c.min_order_amount > 0 else ""
        lines.append(f"• <strong>{c.code}</strong> — {disc} off{min_info}")
        if c.description:
            lines.append(f"  <em>{c.description}</em>")
    return "\n".join(lines)


def _reply_orders(msg):
    return (
        "📦 <strong>Order Tracking:</strong><br><br>"
        "To track your order:<br>"
        "1. <a href=\"/accounts/login/\" style=\"color:#4f46e5\">Log in</a> to your account<br>"
        "2. Go to <a href=\"/accounts/orders/\" style=\"color:#4f46e5\">My Orders</a><br>"
        "3. Click on any order to see status & tracking<br><br>"
        "Need help? Email <strong>support@buyzenix.com</strong>"
    )


def _reply_returns():
    return (
        "↩️ <strong>Return Policy:</strong><br><br>"
        "• Returns accepted within <strong>7 days</strong> of delivery<br>"
        "• Item must be unused and in original packaging<br>"
        "• Refund processed within <strong>3-5 business days</strong><br><br>"
        "To initiate a return:<br>"
        "1. Go to <a href=\"/accounts/orders/\" style=\"color:#4f46e5\">My Orders</a><br>"
        "2. Select the order → Request Return<br><br>"
        "Contact: <strong>support@buyzenix.com</strong>"
    )


def _reply_shipping():
    return (
        "🚚 <strong>Shipping Info:</strong><br><br>"
        "• <strong>Dhaka:</strong> 2-5 business days<br>"
        "• <strong>Outside Dhaka:</strong> 5-7 business days<br>"
        "• <strong>Free shipping</strong> on orders over ৳2,000<br>"
        "• Cash on Delivery (COD) available nationwide<br><br>"
        "Track your order: <a href=\"/accounts/orders/\" style=\"color:#4f46e5\">My Orders</a>"
    )


def _reply_payments():
    return (
        "💳 <strong>Payment Methods:</strong><br><br>"
        "• <strong>bKash</strong> — Mobile banking<br>"
        "• <strong>Nagad</strong> — Mobile banking<br>"
        "• <strong>Credit/Debit Card</strong> — Visa, Mastercard<br>"
        "• <strong>Cash on Delivery (COD)</strong> — Pay when you receive<br><br>"
        "All payments are secure and encrypted."
    )


def _reply_account():
    return (
        "👤 <strong>Account Help:</strong><br><br>"
        "• <a href=\"/accounts/register/\" style=\"color:#4f46e5\">Create Account</a><br>"
        "• <a href=\"/accounts/login/\" style=\"color:#4f46e5\">Login</a><br>"
        "• <a href=\"/accounts/dashboard/\" style=\"color:#4f46e5\">Dashboard</a><br>"
        "• <a href=\"/accounts/orders/\" style=\"color:#4f46e5\">Order History</a><br><br>"
        "Forgot password? Click 'Forgot Password' on the <a href=\"/accounts/login/\" style=\"color:#4f46e5\">login page</a>."
    )


def _reply_contact():
    from dashboard.models import SiteSettings
    try:
        s = SiteSettings.objects.first()
    except Exception:
        s = None

    lines = ["📞 <strong>Contact Us:</strong>"]
    if s:
        if s.contact_email:
            lines.append(f"• Email: <strong>{s.contact_email}</strong>")
        if s.contact_phone:
            lines.append(f"• Phone: <strong>{s.contact_phone}</strong>")
        if s.address:
            lines.append(f"• Address: {s.address}")
        if s.facebook_url:
            lines.append(f"• Facebook: <a href=\"{s.facebook_url}\" style=\"color:#4f46e5\">{s.facebook_url}</a>")
    if len(lines) == 1:
        lines.append("• Email: <strong>support@buyzenix.com</strong>")
        lines.append("• We're available 24/7")
    return "\n".join(lines)


def _reply_warranty():
    return (
        "🛡️ <strong>Warranty Info:</strong><br><br>"
        "• All products come with <strong>manufacturer warranty</strong><br>"
        "• Warranty period varies by product<br>"
        "• Check product page for specific warranty details<br>"
        "• Defective items replaced within <strong>48 hours</strong><br><br>"
        "Contact support for warranty claims: <strong>support@buyzenix.com</strong>"
    )


def _reply_about():
    from dashboard.models import SiteSettings
    from core.models import Product, Category

    try:
        s = SiteSettings.objects.first()
    except Exception:
        s = None

    product_count = Product.objects.filter(available=True).count()
    cat_count = Category.objects.count()

    name = s.site_name if s else "BuyZenix"
    tagline = s.site_tagline if s else "Premium Online Store"

    lines = [
        f"🏢 <strong>{name}</strong>",
        f"<em>{tagline}</em><br><br>",
        f"• <strong>{product_count}</strong> products available",
        f"• <strong>{cat_count}</strong> categories",
        "• Electronics, Fashion, Home & Accessories",
        "• Buy and sell — your zen marketplace<br><br>",
    ]
    if s and s.address:
        lines.append(f"📍 {s.address}")
    return "\n".join(lines)


def _reply_hours():
    return (
        "🕐 <strong>Store Hours:</strong><br><br>"
        "• Online store: <strong>Open 24/7</strong><br>"
        "• Customer support: <strong>24/7</strong> via email<br>"
        "• Orders processed: <strong>Every day</strong><br>"
        "• Delivery: <strong>Business days</strong> (Sun-Thu)"
    )


def _reply_unknown(msg):
    from core.models import Product

    # Try product search as fallback
    words = [w for w in re.findall(r'\b\w+\b', msg.lower()) if len(w) > 2]
    if words:
        q = Q()
        for w in words:
            q |= Q(name__icontains=w) | Q(description__icontains=w) | Q(category__name__icontains=w)
        products = Product.objects.filter(q, available=True)[:3]
        if products:
            lines = [f"🔍 I found these products for '<strong>{msg}</strong>':"]
            for p in products:
                lines.append(f"• <a href=\"{p.get_absolute_url()}\" style=\"color:#4f46e5\">{p.name}</a> — ৳{p.price}")
            lines.append("\nType <strong>help</strong> for more options.")
            return "\n".join(lines)

    return (
        "I'm not sure about that. Try asking about:<br>"
        "• <strong>Products</strong> — what we sell<br>"
        "• <strong>Prices</strong> — product costs<br>"
        "• <strong>Orders</strong> — track your order<br>"
        "• <strong>Shipping</strong> — delivery info<br>"
        "• <strong>Payments</strong> — payment methods<br><br>"
        "Type <strong>help</strong> for all options."
    )


# ─── Intent → Reply mapping ───

_INTENT_MAP = {
    "greeting": lambda m: _reply_greeting(),
    "thanks": lambda m: "You're welcome! Is there anything else I can help with?",
    "bye": lambda m: "Goodbye! Thank you for shopping with BuyZenix. Have a great day! 👋",
    "help": lambda m: _reply_help(),
    "products": _reply_products,
    "categories": lambda m: _reply_categories(),
    "price": _reply_price,
    "featured": lambda m: _reply_featured(),
    "coupons": lambda m: _reply_coupons(),
    "orders": _reply_orders,
    "returns": lambda m: _reply_returns(),
    "shipping": lambda m: _reply_shipping(),
    "payments": lambda m: _reply_payments(),
    "account": lambda m: _reply_account(),
    "contact": lambda m: _reply_contact(),
    "warranty": lambda m: _reply_warranty(),
    "about": lambda m: _reply_about(),
    "hours": lambda m: _reply_hours(),
    "unknown": _reply_unknown,
}


# ─── View ───

HELP_TEXT = (
    "I can help with:\n"
    "• Orders & Tracking\n"
    "• Returns & Refunds\n"
    "• Coupons & Discounts\n"
    "• Payments (bKash, Nagad, COD)\n"
    "• Shipping & Delivery\n"
    "• Account & Login\n"
    "• Products & Categories\n"
    "• Contact Information\n"
)


@csrf_exempt
@require_POST
def chatbot_api(request):
    """Dynamic chatbot — reads real site data from DB to answer."""
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"reply": "Sorry, I couldn't understand that."})

    message = data.get("message", "").strip()
    if not message:
        return JsonResponse({"reply": "Please type a message."})

    intent = _detect_intent(message)
    handler = _INTENT_MAP.get(intent, _reply_unknown)

    try:
        reply = handler(message)
    except Exception:
        reply = "Sorry, something went wrong. Please try again or email support@buyzenix.com"

    return JsonResponse({"reply": reply})
