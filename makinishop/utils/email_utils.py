from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from celery import shared_task
import os

@shared_task(queue='emails')
def send_templated_email(subject, to_email, template_name, context, base_url=None):
    if not base_url:
        base_url = os.environ.get('BASE_URL', 'http://localhost:8000')
    context = dict(context)
    context['base_url'] = base_url
    html_content = render_to_string(f'emails/{template_name}', context)
    text_content = render_to_string(f'emails/{template_name}', {**context, 'plain': True})
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to_email],
    )
    email.attach_alternative(html_content, "text/html")
    email.send()
