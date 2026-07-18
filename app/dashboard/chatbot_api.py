import json
import re

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

# ─── Rule-based chatbot (free, no external dependencies) ───
# Upgrade path: replace with ChatterBot, Rasa, or Botpress via API Control Panel

_PATTERNS = [
    (r"\b(hi|hello|hey|assalam|namaste|good\s*(morning|afternoon|evening))\b",
     "Hello! Welcome to BuyZenix. How can I help you today?"),
    (r"\b(order|my\s*order|track|where)\b",
     "You can track your orders from your dashboard: /accounts/orders/. For help, email support@buyzenix.com."),
    (r"\b(return|refund|exchange)\b",
     "Our return policy: items can be returned within 7 days. Visit /accounts/orders/ to initiate a return."),
    (r"\b(coupon|discount|offer|promo|code)\b",
     "Check our homepage for current promotions! You can also apply coupon codes at checkout."),
    (r"\b(pay|payment|bkash|nagad|card|cod)\b",
     "We accept bKash, Nagad, credit/debit cards, and Cash on Delivery (COD)."),
    (r"\b(ship|delivery|deliver)\b",
     "Standard delivery takes 2-5 business days in Dhaka, 5-7 days outside Dhaka. Free shipping on orders over ৳2000."),
    (r"\b(account|login|register|sign\s*in|password)\b",
     "You can create an account or login at /accounts/login/. For password reset, click 'Forgot Password' on the login page."),
    (r"\b(product|item|what\s*do\s*you|catalog|shop)\b",
     "We have Electronics, Fashion, Home, and Accessories. Browse all products at /products/."),
    (r"\b(contact|phone|email|support|help)\b",
     "Reach us at support@buyzenix.com or call +880-XXXX-XXXX. We're available 24/7."),
    (r"\b(warranty|guarantee)\b",
     "All products come with manufacturer warranty. Check product page for specific warranty details."),
    (r"\b(thank|thanks|shukriya)\b",
     "You're welcome! Is there anything else I can help you with?"),
    (r"\b(bye|goodbye|alvida)\b",
     "Goodbye! Thank you for shopping with BuyZenix. Have a great day!"),
    (r"\b(sale|off|cheap|price)\b",
     "Visit our homepage for current sale items. Use coupon codes at checkout for extra discounts!"),
    (r"\b(location|address|where\s*are\s*you)\b",
     "We're based in Dhaka, Bangladesh. We deliver nationwide!"),
]


def _get_bot_reply(message):
    msg = message.lower().strip()
    for pattern, reply in _PATTERNS:
        if re.search(pattern, msg):
            return reply
    return "I'm not sure I understand. Try asking about orders, payments, shipping, products, or returns. Type 'help' for options."


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
    """Chatbot API endpoint — works without external services."""
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"reply": "Sorry, I couldn't understand that."})

    message = data.get("message", "").strip()
    if not message:
        return JsonResponse({"reply": "Please type a message."})

    if message.lower() in ("help", "?", "options"):
        reply = HELP_TEXT
    else:
        reply = _get_bot_reply(message)

    return JsonResponse({"reply": reply})
