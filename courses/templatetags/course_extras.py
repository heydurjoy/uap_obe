from django import template
from accounts.models import Holiday

register = template.Library()

@register.filter
def get_holiday(date):
    """
    Get the holiday object for a given date
    """
    return Holiday.objects.filter(
        start_date__lte=date,
        end_date__gte=date
    ).first() 