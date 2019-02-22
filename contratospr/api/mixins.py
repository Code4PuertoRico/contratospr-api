from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

CACHE_TIME = 60 * 15


class CachedAPIViewMixin:
    @method_decorator(cache_page(CACHE_TIME))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
