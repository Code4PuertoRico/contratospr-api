import datetime
import json
import os

import configurations
import dramatiq
from dramatiq.brokers.redis import RedisBroker

configuration = os.getenv("ENVIRONMENT", "development").title()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "contratospr.settings")
os.environ.setdefault("DJANGO_CONFIGURATION", configuration)

configurations.setup()

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


redis_broker = RedisBroker(url=settings.BROKER_URL)
dramatiq.set_broker(redis_broker)
dramatiq.set_encoder(DramatiqJSONEncoder())
