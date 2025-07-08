from django import template
register = template.Library()

@register.filter
def dict_get(d, key):
    # Support tuple keys passed as 'student_id,item_id' string
    if isinstance(key, str) and ',' in key:
        parts = key.split(',')
        try:
            key = (int(parts[0]), int(parts[1]))
        except Exception:
            key = tuple(parts)
    return d.get(key) 