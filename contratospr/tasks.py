import datetime
import json
import os

import configurations
import dramatiq
from dramatiq.brokers.redis import RedisBroker
from dramatiq.middleware import Middleware

configuration = os.getenv("ENVIRONMENT", "development").title()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "contratospr.settings")
os.environ.setdefault("DJANGO_CONFIGURATION", configuration)

configurations.setup()

from django import db  # noqa isort:skip
from django.conf import settings  # noqa isort:skip


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            representation = obj.isoformat()
            if representation.endswith("+00:00"):
                representation = representation[:-6] + "Z"
            return representation

        return super(JSONEncoder, self).default(obj)


class DramatiqJSONEncoder(dramatiq.JSONEncoder):
    def encode(self, data):
        return json.dumps(data, separators=(",", ":"), cls=JSONEncoder).encode("utf-8")


class DbConnectionsMiddleware(Middleware):
    def _close_connections(self, *args, **kwargs):
        db.connections.close_all()

    before_consumer_thread_shutdown = _close_connections
    before_worker_thread_shutdown = _close_connections
    before_worker_shutdown = _close_connections


broker = RedisBroker(url=settings.BROKER_URL)
broker.add_middleware(DbConnectionsMiddleware())
dramatiq.set_broker(broker)
dramatiq.set_encoder(DramatiqJSONEncoder())
