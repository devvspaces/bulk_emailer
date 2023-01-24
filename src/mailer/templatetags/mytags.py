from django import template

register = template.Library()


@register.simple_tag()
def get(value):
    if value:
        return value
    return ''
