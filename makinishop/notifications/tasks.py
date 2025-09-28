from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import NotificationQueue
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_notification_email(self, queue_id):
    try:
        queue = NotificationQueue.objects.get(id=queue_id)
        if queue.status != 'pending':
            return
        # Example: Render subject/body from template and context
        subject = queue.template.subject_template.format(**queue.context)
        body = queue.template.body_template.format(**queue.context)
        recipient = queue.context.get('email')
        if not recipient:
            queue.status = 'failed'
            queue.error = 'No recipient email in context.'
            queue.save()
            return
        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [recipient],
            fail_silently=False
        )
        queue.status = 'sent'
        queue.save()
    except Exception as exc:
        logger.error(f"Notification send failed: {exc}")
        if queue:
            queue.status = 'failed'
            queue.error = str(exc)
            queue.save()
        self.retry(exc=exc)
