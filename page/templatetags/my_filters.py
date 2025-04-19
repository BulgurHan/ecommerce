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


@register.filter
def mask_email(email):
    try:
        local, domain = email.split('@')
        masked_local = local[0] + '*' * (len(local) - 1)
        domain_parts = domain.split('.')
        masked_domain = '*' * len(domain_parts[0])  # örneğin gmail → *****
        return f"{masked_local}@{masked_domain}.{domain_parts[1]}"
    except:
        return email  # Eğer bir hata olursa, orijinali döndür