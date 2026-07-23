import json
import re
from difflib import SequenceMatcher

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db.models import Q, Avg, Min, Max, Count


def _fuzzy_match(word, target, threshold=0.7):
    """Check if word is close to target (handles typos)."""
    if word == target:
        return True
    if target.startswith(word) or word.startswith(target[:3]):
        return True
    return SequenceMatcher(None, word, target).ratio() >= threshold


def _contains_any(msg, words):
    """Check if message contains any of the words (with typo tolerance)."""
    for w in words:
        if re.search(r'\b' + re.escape(w[:3]) + r'\w*\b', msg):
            return True
    return False


# ─── Intent detection ───

def _detect_intent(msg):
    m = msg.lower().strip()
    m_clean = re.sub(r'[^\w\s]', ' ', m)

    if re.search(r'\b(hi|hello|hey|assalam|namaste|good\s*(morning|afternoon|evening)|yo|sup)\b', m):
        return "greeting"
    if re.search(r'\b(thank|thanks|shukriya|tq)\b', m):
        return "thanks"
    if re.search(r'\b(bye|goodbye|alvida|see\s*you)\b', m):
        return "bye"
    if re.search(r'\b(help|what\s*can|options|menu)\b', m):
        return "help"
    if re.search(r'\b(who|about|what\s*is\s*buyzenix|tell\s*me\s*about|company)\b', m):
        return "about"

    # ── Count / total queries ──
    if re.search(r'\b(how\s*(many|much)|count|total|number\s*of|koto|kitne)\b', m):
        return "count"

    # ── Price sorting queries (lowest/cheapest first) ──
    if re.search(r'\b(low|cheapest|min|lowest|sasta|kam)\b.*\b(price|cost|taka|product|list|name)\b', m):
        return "price_low"
    if re.search(r'\b(price|cost|taka)\b.*\b(low|cheapest|min|lowest|sasta|kam)\b', m):
        return "price_low"
    if re.search(r'\b(low\s*price|low\s*cost|cheapest|lowest|sasta)\b', m):
        return "price_low"

    # ── Price sorting queries (highest/most expensive first) ──
    if re.search(r'\b(high|expensive|max|highest|mehanga|zyada)\b.*\b(price|cost|taka|product|list|name)\b', m):
        return "price_high"
    if re.search(r'\b(price|cost|taka)\b.*\b(high|expensive|max|highest|mehanga|zyada)\b', m):
        return "price_high"
    if re.search(r'\b(high\s*price|expensive|costliest|highest|premium)\b', m):
        return "price_high"

    # ── Generic price query ──
    if re.search(r'\b(price|cost|how\s*much|taka|bdt|৳|\$)\b', m):
        return "price"

    # ── Specific product search ──
    if re.search(r'\b(search|find|look|show)\b', m):
        return "search"

    # ── In-stock / availability ──
    if re.search(r'\b(in\s*stock|available|out\s*of\s*stock|stock|achhe|ache)\b', m):
        return "stock"

    # ── Sale / discount ──
    if re.search(r'\b(sale|discount|offer|promo|coupon|code|off|deal|cheap)\b', m):
        return "coupons"

    # ── New / latest (typo-tolerant: "nre", "nw", "neww", "taday", "todat") ──
    new_words = ['new', 'latest', 'recent', 'arrivals', 'newest', 'nre', 'nw', 'neww', 'nwe', 'just', 'taday', 'todat', 'today']
    for w in new_words:
        if re.search(r'\b' + re.escape(w) + r'\w*\b', m_clean):
            return "latest"

    # ── Featured / popular / trending ──
    if re.search(r'\b(feature|popular|best|top|recommend|trending|trend)\b', m):
        return "featured"

    # ── Categories ──
    if re.search(r'\b(categor|cat|type|group|section|what\s*do\s*you\s*have)\b', m):
        return "categories"

    # ── Product names list ──
    if re.search(r'\b(product\s*name|all\s*product|list\s*product|name\s*of\s*product|ki\s*ki\s*product|what\s*product)\b', m):
        return "product_names"

    # ── General product listing ──
    if re.search(r'\b(product|item|sell|catalog|shop|browse|what\s*(do|have|is))\b', m):
        return "products"

    # ── Orders ──
    if re.search(r'\b(order|my\s*order|track|where|status|shipped)\b', m):
        return "orders"

    # ── Returns ──
    if re.search(r'\b(return|refund|exchange|money\s*back)\b', m):
        return "returns"

    # ── Shipping ──
    if re.search(r'\b(ship|delivery|deliver|courier|parcels?)\b', m):
        return "shipping"

    # ── Payments ──
    if re.search(r'\b(pay|payment|bkash|nagad|card|cod|cash|visa|mastercard)\b', m):
        return "payments"

    # ── Account ──
    if re.search(r'\b(account|login|register|sign\s*in|password|profile|signup)\b', m):
        return "account"

    # ── Contact ──
    if re.search(r'\b(contact|phone|email|support|reach|call)\b', m):
        return "contact"

    # ── Warranty ──
    if re.search(r'\b(warranty|guarantee|defect|broken|quality)\b', m):
        return "warranty"

    # ── Hours ──
    if re.search(r'\b(operating|open|hour|time)\b', m):
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
        "• <strong>Products</strong> — ask what we sell\n"
        "• <strong>Categories</strong> — browse Electronics, Fashion, Home\n"
        "• <strong>Prices</strong> — low price, high price, cheapest\n"
        "• <strong>Count</strong> — how many products?\n"
        "• <strong>Stock</strong> — check availability\n"
        "• <strong>Featured</strong> — top products\n"
        "• <strong>Latest</strong> — new arrivals\n"
        "• <strong>Search</strong> — find specific products\n"
        "• <strong>Coupons</strong> — active discounts\n"
        "• <strong>Orders</strong> — track your order\n"
        "• <strong>Shipping</strong> — delivery info\n"
        "• <strong>Payments</strong> — bKash, Nagad, COD\n"
        "• <strong>Returns</strong> — return policy\n"
        "• <strong>Contact</strong> — reach support"
    )


def _reply_count():
    from core.models import Product, Category

    total = Product.objects.filter(available=True).count()
    featured = Product.objects.filter(available=True, featured=True).count()
    cats = Category.objects.annotate(cnt=Count('products')).filter(cnt__gt=0)

    lines = [f"📊 <strong>Product Summary:</strong>"]
    lines.append(f"• Total products: <strong>{total}</strong>")
    lines.append(f"• Featured: <strong>{featured}</strong>")
    lines.append(f"• Categories with products: <strong>{cats.count()}</strong>")
    lines.append("")
    for c in cats:
        lines.append(f"• {c.name}: <strong>{c.cnt}</strong> products")
    return "\n".join(lines)


def _reply_price_low():
    from core.models import Product

    products = Product.objects.filter(available=True).order_by('price')[:5]
    if not products:
        return "No products available."

    total = Product.objects.filter(available=True).count()
    lines = [f"💰 <strong>Lowest priced products ({total} total):</strong>"]
    for i, p in enumerate(products, 1):
        stock = f"{p.stock} in stock" if p.stock > 0 else "out of stock"
        tag = " ⭐ Featured" if p.featured else ""
        lines.append(f"{i}. <a href=\"{p.get_absolute_url()}\" style=\"color:#4f46e5\">{p.name}</a> — <strong>৳{p.price}</strong> ({stock}){tag}")
    lines.append(f"\nSee all sorted: <a href=\"/products/?sort_price=low_to_high\" style=\"color:#4f46e5\">Low → High</a>")
    return "\n".join(lines)


def _reply_price_high():
    from core.models import Product

    products = Product.objects.filter(available=True).order_by('-price')[:5]
    if not products:
        return "No products available."

    lines = ["💰 <strong>Highest priced products:</strong>"]
    for i, p in enumerate(products, 1):
        stock = f"{p.stock} in stock" if p.stock > 0 else "out of stock"
        lines.append(f"{i}. <a href=\"{p.get_absolute_url()}\" style=\"color:#4f46e5\">{p.name}</a> — <strong>৳{p.price}</strong> ({stock})")
    lines.append(f"\nSee all sorted: <a href=\"/products/?sort_price=high_to_low\" style=\"color:#4f46e5\">High → Low</a>")
    return "\n".join(lines)


def _reply_price(msg):
    from core.models import Product

    words = [w for w in re.findall(r'\b\w+\b', msg.lower()) if len(w) > 2]
    skip = {'price', 'cost', 'how', 'much', 'taka', 'bdt', 'expensive', 'cheap', 'afford', 'budget',
            'the', 'what', 'is', 'of', 'for', 'give', 'tell', 'show', 'about'}
    keywords = [w for w in words if w not in skip]

    if keywords:
        q = Q()
        for kw in keywords:
            q |= Q(name__icontains=kw) | Q(description__icontains=kw)
        products = Product.objects.filter(q, available=True).order_by('price')[:5]
        if products:
            lines = [f"💰 <strong>Price for '{' '.join(keywords)}':</strong>"]
            for p in products:
                price = f"<strong>৳{p.price}</strong>"
                if p.sale_price and p.sale_price < p.price:
                    discount = int((1 - p.sale_price / p.price) * 100)
                    price = f"~~৳{p.price}~~ → <strong>৳{p.sale_price}</strong> ({discount}% off!)"
                stock = f"{p.stock} in stock" if p.stock > 0 else "out of stock"
                lines.append(f"• <a href=\"{p.get_absolute_url()}\" style=\"color:#4f46e5\">{p.name}</a> — {price} ({stock})")
            return "\n".join(lines)

    stats = Product.objects.filter(available=True).aggregate(
        min_price=Min('price'), max_price=Max('price'), avg_price=Avg('price'), cnt=Count('id')
    )
    if stats['min_price']:
        return (
            f"💰 <strong>Price Overview ({stats['cnt']} products):</strong><br>"
            f"• Lowest: <strong>৳{stats['min_price']}</strong><br>"
            f"• Highest: <strong>৳{stats['max_price']}</strong><br>"
            f"• Average: <strong>৳{int(stats['avg_price'])}</strong><br><br>"
            f"<a href=\"/products/?sort_price=low_to_high\" style=\"color:#4f46e5\">Low → High</a> | "
            f"<a href=\"/products/?sort_price=high_to_low\" style=\"color:#4f46e5\">High → Low</a>"
        )
    return "No products available yet."


def _reply_search(msg):
    from core.models import Product

    words = [w for w in re.findall(r'\b\w+\b', msg.lower()) if len(w) > 2]
    skip = {'search', 'find', 'look', 'show', 'me', 'the', 'for', 'product', 'products'}
    keywords = [w for w in words if w not in skip]

    if not keywords:
        return "What are you looking for? Try: <strong>search earbuds</strong> or <strong>find keyboard</strong>"

    q = Q()
    for kw in keywords:
        q |= Q(name__icontains=kw) | Q(description__icontains=kw) | Q(category__name__icontains=kw)
    products = Product.objects.filter(q, available=True)[:5]

    if products:
        lines = [f"🔍 <strong>Found {products.count()} results for '{' '.join(keywords)}':</strong>"]
        for p in products:
            price = f"৳{p.price}"
            if p.sale_price and p.sale_price < p.price:
                price = f"<s>৳{p.price}</s> → <strong>৳{p.sale_price}</strong>"
            lines.append(f"• <a href=\"{p.get_absolute_url()}\" style=\"color:#4f46e5\">{p.name}</a> — {price}")
        return "\n".join(lines)

    return f"🔍 No products found for '{' '.join(keywords)}'. Try different keywords or browse <a href=\"/products/\" style=\"color:#4f46e5\">all products</a>."


def _reply_stock():
    from core.models import Product

    in_stock = Product.objects.filter(available=True, stock__gt=0).count()
    out_stock = Product.objects.filter(available=True, stock=0).count()
    low_stock = Product.objects.filter(available=True, stock__gt=0, stock__lte=5).order_by('stock')[:5]

    lines = [f"📦 <strong>Stock Status:</strong>"]
    lines.append(f"• In stock: <strong>{in_stock}</strong> products")
    lines.append(f"• Out of stock: <strong>{out_stock}</strong> products")

    if low_stock:
        lines.append(f"\n⚠️ <strong>Low stock (≤5 left):</strong>")
        for p in low_stock:
            lines.append(f"• {p.name}: <strong>{p.stock}</strong> left")

    return "\n".join(lines)


def _reply_product_names():
    from core.models import Product

    products = Product.objects.filter(available=True).order_by('name')
    if not products:
        return "No products available."

    lines = [f"📋 <strong>All {products.count()} Product Names:</strong>"]
    for i, p in enumerate(products, 1):
        stock = "✅" if p.stock > 0 else "❌"
        price = f"৳{p.sale_price}" if p.sale_price and p.sale_price < p.price else f"৳{p.price}"
        lines.append(f"{i}. {stock} {p.name} — {price}")
    return "\n".join(lines)


def _reply_featured():
    from core.models import Product

    featured = Product.objects.filter(available=True, featured=True).order_by('-created')[:5]
    if not featured:
        return "No featured products right now."

    lines = ["⭐ <strong>Featured Products:</strong>"]
    for p in featured:
        price = f"৳{p.price}"
        if p.sale_price and p.sale_price < p.price:
            price = f"<s>৳{p.price}</s> → <strong>৳{p.sale_price}</strong>"
        stock = f"{p.stock} in stock" if p.stock > 0 else "out of stock"
        lines.append(f"• <a href=\"{p.get_absolute_url()}\" style=\"color:#4f46e5\">{p.name}</a> — {price} ({stock})")
    return "\n".join(lines)


def _reply_latest():
    from core.models import Product

    products = Product.objects.filter(available=True).order_by('-created')[:5]
    if not products:
        return "No products yet."

    lines = ["🆕 <strong>Latest Arrivals:</strong>"]
    for p in products:
        price = f"৳{p.price}"
        if p.sale_price and p.sale_price < p.price:
            price = f"<s>৳{p.price}</s> → <strong>৳{p.sale_price}</strong>"
        lines.append(f"• <a href=\"{p.get_absolute_url()}\" style=\"color:#4f46e5\">{p.name}</a> — {price}")
    return "\n".join(lines)


def _reply_categories():
    from core.models import Category

    cats = Category.objects.annotate(cnt=Count('products', filter=Q(products__available=True))).filter(cnt__gt=0)
    if not cats:
        cats = Category.objects.all()
    if not cats:
        return "No categories yet."

    total = sum(c.cnt for c in cats)
    lines = [f"📂 <strong>Categories ({total} products total):</strong>"]
    for c in cats:
        lines.append(f"• <a href=\"{c.get_absolute_url()}\" style=\"color:#4f46e5\">{c.name}</a> — {c.cnt} products")
    lines.append(f"\nBrowse: <a href=\"/products/\" style=\"color:#4f46e5\">All Products</a>")
    return "\n".join(lines)


def _reply_products(msg):
    from core.models import Product, Category
    import re as _re

    m = msg.lower().strip()

    # Check for category filter
    cats = Category.objects.all()
    cat_filter = None
    for c in cats:
        if c.name.lower() in m:
            cat_filter = c
            break

    # Extract meaningful keywords (filter out filler words)
    words = [w for w in _re.findall(r'\b\w+\b', m) if len(w) > 2]
    skip = {'product', 'item', 'sell', 'available', 'stock', 'what', 'do', 'have',
            'is', 'catalog', 'shop', 'browse', 'tell', 'show', 'give', 'your',
            'the', 'some', 'any', 'all', 'with', 'for', 'and', 'products', 'things',
            'today', 'taday', 'todat', 'new', 'nre', 'nw', 'just', 'any', 'there',
            'something', 'really', 'actually', 'like', 'want', 'need', 'looking',
            'that', 'this', 'those', 'these', 'can', 'you', 'me', 'about', 'from',
            'please', 'could', 'would', 'also', 'only', 'still'}
    keywords = [w for w in words if w not in skip]

    qs = Product.objects.filter(available=True)
    if cat_filter:
        qs = qs.filter(category=cat_filter)
    if keywords:
        q = Q()
        for kw in keywords:
            q |= Q(name__icontains=kw) | Q(description__icontains=kw)
        qs = qs.filter(q)

    products = qs.order_by('price')[:8]
    if not products:
        products = Product.objects.filter(available=True).order_by('price')[:8]

    if not products:
        return "No products available right now. Check back soon!"

    label = f"in {cat_filter.name}" if cat_filter else ""
    label += f" matching '{' '.join(keywords)}'" if keywords else ""
    lines = [f"📦 <strong>{products.count()} products found{label}:</strong>"]
    for p in products:
        price = f"৳{p.price}"
        if p.sale_price and p.sale_price < p.price:
            price = f"<s>৳{p.price}</s> → <strong>৳{p.sale_price}</strong> ⭐"
        stock_info = f"({p.stock} in stock)" if p.stock > 0 else "<em>out of stock</em>"
        lines.append(f"• <a href=\"{p.get_absolute_url()}\" style=\"color:#4f46e5\">{p.name}</a> — {price} {stock_info}")

    lines.append(f"\nBrowse all: <a href=\"/products/\" style=\"color:#4f46e5\">View Catalog →</a>")
    return "\n".join(lines)


def _reply_coupons():
    from dashboard.models import Coupon
    from django.utils import timezone

    now = timezone.now()
    active = Coupon.objects.filter(
        Q(valid_from__lte=now) | Q(valid_from__isnull=True),
        Q(valid_to__gte=now) | Q(valid_to__isnull=True),
        is_active=True,
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
        "1. <a href=\"/accounts/login/\" style=\"color:#4f46e5\">Log in</a><br>"
        "2. Go to <a href=\"/accounts/orders/\" style=\"color:#4f46e5\">My Orders</a><br>"
        "3. Click any order to see status<br><br>"
        "Need help? Email <strong>support@buyzenix.com</strong>"
    )


def _reply_returns():
    return (
        "↩️ <strong>Return Policy:</strong><br><br>"
        "• Returns within <strong>7 days</strong> of delivery<br>"
        "• Item must be unused, original packaging<br>"
        "• Refund in <strong>3-5 business days</strong><br><br>"
        "Start return: <a href=\"/accounts/orders/\" style=\"color:#4f46e5\">My Orders</a>"
    )


def _reply_shipping():
    return (
        "🚚 <strong>Shipping:</strong><br><br>"
        "• <strong>Dhaka:</strong> 2-5 business days<br>"
        "• <strong>Outside Dhaka:</strong> 5-7 days<br>"
        "• <strong>Free shipping</strong> on orders over ৳2,000<br>"
        "• COD available nationwide"
    )


def _reply_payments():
    return (
        "💳 <strong>Payments:</strong><br><br>"
        "• <strong>bKash</strong> — Mobile banking<br>"
        "• <strong>Nagad</strong> — Mobile banking<br>"
        "• <strong>Credit/Debit Card</strong> — Visa, Mastercard<br>"
        "• <strong>Cash on Delivery</strong> — Pay on receipt"
    )


def _reply_account():
    return (
        "👤 <strong>Account:</strong><br><br>"
        "• <a href=\"/accounts/register/\" style=\"color:#4f46e5\">Create Account</a><br>"
        "• <a href=\"/accounts/login/\" style=\"color:#4f46e5\">Login</a><br>"
        "• <a href=\"/accounts/dashboard/\" style=\"color:#4f46e5\">Dashboard</a><br>"
        "• <a href=\"/accounts/orders/\" style=\"color:#4f46e5\">Order History</a>"
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
    if len(lines) == 1:
        lines.append("• Email: <strong>support@buyzenix.com</strong>")
    return "\n".join(lines)


def _reply_warranty():
    return (
        "🛡️ <strong>Warranty:</strong><br><br>"
        "• All products have <strong>manufacturer warranty</strong><br>"
        "• Defective items replaced in <strong>48 hours</strong><br>"
        "• Check product page for details"
    )


def _reply_about():
    from dashboard.models import SiteSettings
    from core.models import Product, Category

    try:
        s = SiteSettings.objects.first()
    except Exception:
        s = None

    p_count = Product.objects.filter(available=True).count()
    c_count = Category.objects.annotate(cnt=Count('products')).filter(cnt__gt=0).count()
    name = s.site_name if s else "BuyZenix"
    tagline = s.site_tagline if s else "Premium Online Store"

    lines = [f"🏢 <strong>{name}</strong>", f"<em>{tagline}</em><br><br>",
             f"• <strong>{p_count}</strong> products | <strong>{c_count}</strong> categories",
             "• Electronics, Fashion, Home & Accessories",
             "• Buy and sell — your zen marketplace"]
    if s and s.address:
        lines.append(f"📍 {s.address}")
    return "\n".join(lines)


def _reply_hours():
    return "🕐 <strong>Store:</strong> Open 24/7 online. Support: 24/7 via email. Delivery: business days."


def _reply_unknown(msg):
    from core.models import Product

    # Product name search fallback
    words = [w for w in re.findall(r'\b\w+\b', msg.lower().strip('?!.') if isinstance(msg, str) else '') if len(w) > 2]
    skip = {'how', 'many', 'much', 'what', 'can', 'you', 'tell', 'give', 'show',
            'about', 'the', 'are', 'there', 'any', 'some', 'all', 'name', 'list',
            'today', 'have', 'taday', 'nre', 'just', 'there', 'something'}
    keywords = [w for w in words if w not in skip]

    if keywords:
        q = Q()
        for w in keywords:
            q |= Q(name__icontains=w) | Q(description__icontains=w) | Q(category__name__icontains=w)
        products = Product.objects.filter(q, available=True)[:3]
        if products:
            lines = [f"🔍 Found for '<strong>{' '.join(keywords)}</strong>':"]
            for p in products:
                price = f"৳{p.sale_price}" if p.sale_price and p.sale_price < p.price else f"৳{p.price}"
                lines.append(f"• <a href=\"{p.get_absolute_url()}\" style=\"color:#4f46e5\">{p.name}</a> — {price}")
            lines.append("\nType <strong>help</strong> for more options.")
            return "\n".join(lines)

    return (
        "I didn't understand that. Try:<br>"
        "• <strong>new products</strong> — latest arrivals<br>"
        "• <strong>low price</strong> — cheapest products<br>"
        "• <strong>how many products</strong> — total count<br>"
        "• <strong>search [keyword]</strong> — find products<br>"
        "• Type <strong>help</strong> for all options"
    )


# ─── Intent → Reply mapping ───

_INTENT_MAP = {
    "greeting": lambda m: _reply_greeting(),
    "thanks": lambda m: "You're welcome! Anything else?",
    "bye": lambda m: "Goodbye! 👋",
    "help": lambda m: _reply_help(),
    "about": lambda m: _reply_about(),
    "count": lambda m: _reply_count(),
    "price_low": lambda m: _reply_price_low(),
    "price_high": lambda m: _reply_price_high(),
    "price": _reply_price,
    "search": _reply_search,
    "stock": lambda m: _reply_stock(),
    "product_names": lambda m: _reply_product_names(),
    "featured": lambda m: _reply_featured(),
    "latest": lambda m: _reply_latest(),
    "categories": lambda m: _reply_categories(),
    "products": _reply_products,
    "coupons": lambda m: _reply_coupons(),
    "orders": _reply_orders,
    "returns": lambda m: _reply_returns(),
    "shipping": lambda m: _reply_shipping(),
    "payments": lambda m: _reply_payments(),
    "account": lambda m: _reply_account(),
    "contact": lambda m: _reply_contact(),
    "warranty": lambda m: _reply_warranty(),
    "hours": lambda m: _reply_hours(),
    "unknown": _reply_unknown,
}


# ─── View ───

@csrf_exempt
@require_POST
def chatbot_api(request):
    """Dynamic chatbot — reads real site data from DB."""
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
        reply = "Sorry, something went wrong. Please try again."

    return JsonResponse({"reply": reply})
