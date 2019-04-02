import os

import configurations
import structlog
from celery import Celery
from celery.signals import task_prerun

configuration = os.getenv("ENVIRONMENT", "development").title()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "contratospr.settings")
os.environ.setdefault("DJANGO_CONFIGURATION", configuration)

configurations.setup()

from django.conf import settings  # noqa isort:skip


@task_prerun.connect
def configure_structlog(sender, body=None, **kwargs):
    logger = structlog.get_logger("contratospr.tasks")
    logger.new(task_id=kwargs["task_id"], task_name=sender.__name__)


app = Celery("contratospr")
app.config_from_object(settings, namespace="CELERY")
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
