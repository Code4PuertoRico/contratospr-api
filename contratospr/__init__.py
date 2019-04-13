from __future__ import absolute_import, unicode_literals

from .tasks import app as celery_app  # noqa

__all__ = ("celery_app",)
