from django import template

from shop.models import Order

register = template.Library()

STATUS_ORDER = [c for c, _ in Order.Status.choices if c != Order.Status.CANCELLED]


@register.filter
def status_index(order):
    """Position of the order's status in the fulfilment timeline (for the progress bar)."""
    try:
        return STATUS_ORDER.index(order.status)
    except ValueError:
        return -1
