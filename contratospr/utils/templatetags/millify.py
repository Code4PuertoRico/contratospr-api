import math

from django import template

register = template.Library()

MILLNAMES = ["", "k", "M", "B", "T", "P", "E", "Z", "Y"]


@register.filter
def millify(n):
    most_significant_part = math.floor(0 if n == 0 else math.log10(abs(n)) / 3)
    millidx = max(0, min(len(MILLNAMES) - 1, int(most_significant_part)))
    result = n / 10 ** (3 * millidx)

    return f"{result:.0f}{MILLNAMES[millidx]}"
