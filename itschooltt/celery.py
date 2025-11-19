from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "itschooltt.settings")

current_app = Celery(
    "celery",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    broker_connection_retry_on_startup=True,
)

# current_app.config_from_object("django.conf:settings", namespace="CELERY")

current_app.autodiscover_tasks()
