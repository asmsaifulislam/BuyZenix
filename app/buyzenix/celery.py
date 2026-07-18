import logging

from celery import Celery

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "buyzenix.settings")

app = Celery("buyzenix")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

logger = logging.getLogger(__name__)


@app.task(bind=True)
def debug_task(self):
    logger.debug("Request: %r", self.request)
