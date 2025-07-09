# okada_backend/celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings 

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okada_backend.settings')

app = Celery('okada_backend')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

from okada_backend.celery_config import CELERY_BEAT_SCHEDULE
app.conf.beat_schedule = CELERY_BEAT_SCHEDULE

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
