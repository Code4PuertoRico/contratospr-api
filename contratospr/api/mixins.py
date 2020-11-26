import hashlib
from django.conf import settings
from django.core.cache import cache
from django.utils.encoding import iri_to_uri

CACHE_PREFIX = "views.cache"


def get_cache_key(request):
    uri = iri_to_uri(request.build_absolute_uri())
    hash_key = f"{request.method}.{uri}"
    request_hash = hashlib.md5(hash_key.encode("ascii"))
    return f"{CACHE_PREFIX}.{request_hash.hexdigest()}"


class CachedAPIViewMixin:
    def dispatch(self, request, *args, **kwargs):
        cache_key = get_cache_key(request)
        response = cache.get(cache_key)
        if response:
            return response

        response = super().dispatch(request, *args, **kwargs)

        if response.status_code == 200:
            response.add_post_render_callback(
                lambda r: self._cache_response(r, cache_key)
            )

        return response

    def _cache_response(self, response, cache_key):
        cache.set(cache_key, response, settings.API_CACHE_TIMEOUT)
        return None
