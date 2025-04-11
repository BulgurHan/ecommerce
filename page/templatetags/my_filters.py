from django import template

register = template.Library()

@register.filter
def mask_name(full_name):
    parts = full_name.split()
    masked = []
    for part in parts:
        if len(part) > 0:
            masked.append(part[0] + '*' * (len(part) - 1))
        else:
            masked.append('')
    return ' '.join(masked)