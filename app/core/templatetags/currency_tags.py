from decimal import Decimal

from django import template
from django.conf import settings

register = template.Library()


def convert(amount, code=None):
    """Convert a base (BDT) amount into the given (or default) currency."""
    if code is None:
        code = settings.DEFAULT_CURRENCY
    rate = settings.CURRENCIES[code]["rate"]
    return Decimal(amount) * Decimal(str(rate))


@register.simple_tag(takes_context=True)
def money(context, amount, code=None):
    """Format an amount (stored in BDT) using the active currency."""
    if code is None:
        currency = context.get("currency") or settings.CURRENCIES[
            settings.DEFAULT_CURRENCY
        ]
    else:
        currency = settings.CURRENCIES[code]
    try:
        value = Decimal(amount) * Decimal(str(currency["rate"]))
    except (TypeError, ValueError):
        return str(amount)
    return f"{currency['symbol']}{value:,.2f}"
