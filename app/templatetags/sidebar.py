from django import template
from django.core.cache import cache

register = template.Library()

@register.inclusion_tag("partials/popular_tags.html")
def popular_tags():
    tags = cache.get("popular_tags", [])
    return {"popular_tags": tags}

@register.inclusion_tag("partials/best_members.html")
def best_members():
    users = cache.get("best_members", [])
    return {"best_members": users}
