from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrdc.settings')

app = Celery('HRDC', broker='redis:///1')
app.config_from_object('django.conf:settings', namespace="CELERY")

app.autodiscover_tasks()
