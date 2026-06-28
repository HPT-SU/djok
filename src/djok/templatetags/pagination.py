from django import template
from django.core.paginator import Paginator

register = template.Library()


@register.filter
def elided_page_range(paginator: Paginator, current_page: int):
    return paginator.get_elided_page_range(
        number=current_page,
        on_each_side=2,
        on_ends=1,
    )
