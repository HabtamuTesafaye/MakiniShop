import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'makinishop.settings')

app = Celery('makinishop')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Define multiple queues
from kombu import Queue
app.conf.task_queues = (
    Queue('default'),
    Queue('emails'),
    Queue('notifications'),
    Queue('ai'),
)

# Route tasks to queues
app.conf.task_routes = {
    'notifications.tasks.send_notification_email': {'queue': 'emails'},
    # Add more task routes as needed
}

app.autodiscover_tasks()
