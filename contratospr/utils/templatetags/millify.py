import math

from django import template

register = template.Library()

MILLNAMES = ["", "k", "M", "B", "T", "P", "E", "Z", "Y"]


@register.filter
def millify(value=0):
    number = value or 0
    most_significant_part = math.floor(
        0 if number == 0 else math.log10(abs(number)) / 3
    )
    millidx = max(0, min(len(MILLNAMES) - 1, int(most_significant_part)))
    result = number / 10 ** (3 * millidx)

    return f"{result:.0f}{MILLNAMES[millidx]}"
