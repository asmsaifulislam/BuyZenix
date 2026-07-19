from django.conf import settings


def currency_context(request):
    code = request.session.get("currency", settings.DEFAULT_CURRENCY)
    currencies = settings.CURRENCIES
    currency = currencies.get(code, currencies[settings.DEFAULT_CURRENCY])
    return {
        "currency": currency,
        "currency_code": code,
        "currencies": currencies,
    }


def nav_categories(request):
    from core.models import Category
    return {"nav_categories": Category.objects.all()[:20]}
