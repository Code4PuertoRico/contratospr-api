from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page


class CachedAPIViewMixin:
    @method_decorator(cache_page(settings.API_CACHE_TIMEOUT))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
