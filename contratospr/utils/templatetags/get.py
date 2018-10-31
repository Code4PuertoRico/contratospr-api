from django import template

register = template.Library()


@register.filter
def get(obj, key):
    return obj[key]
