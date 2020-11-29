import hashlib

from django.conf import settings
from django.core.cache import cache
from django.utils.encoding import iri_to_uri

CACHE_PREFIX = "views.cache"
CACHE_HEADER_LIST = ["Accept", "Content-Type"]


def get_cache_key(request):
    headers_hash = hashlib.md5()
    for header in CACHE_HEADER_LIST:
        value = request.headers.get(header)
        if value is not None:
            headers_hash.update(value.encode())

    uri = iri_to_uri(request.build_absolute_uri())
    hash_key = f"{request.method}.{uri}"
    request_hash = hashlib.md5(hash_key.encode())
    return f"{CACHE_PREFIX}.{headers_hash.hexdigest()}.{request_hash.hexdigest()}"


def cache_response(response, cache_key):
    """
    Note: It's important to return `None` here to avoid
    changing return value of .render()
    """
    cache.set(cache_key, response, settings.API_CACHE_TIMEOUT)
    return None


class CachedAPIViewMixin:
    def dispatch(self, request, *args, **kwargs):
        cache_key = get_cache_key(request)
        response = cache.get(cache_key)
        if response:
            return response

        response = super().dispatch(request, *args, **kwargs)

        if response.status_code == 200:
            response.add_post_render_callback(lambda r: cache_response(r, cache_key))

        return response
