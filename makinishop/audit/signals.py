# audit/signals.py
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.apps import apps
from .models import AuditLog
import json
from datetime import datetime
from decimal import Decimal

TRACKED_MODELS = ['Product', 'Category', 'Wishlist', 'FeaturedProduct']

def model_to_dict(instance):
    data = {}
    for field in instance._meta.fields:
        value = getattr(instance, field.name)
        if isinstance(value, datetime):
            data[field.name] = value.isoformat()
        elif isinstance(value, Decimal):
            data[field.name] = float(value)
        else:
            data[field.name] = value
    return data

@receiver(post_save)
def create_update_audit_log(sender, instance, created, **kwargs):
    if sender.__name__ not in TRACKED_MODELS:
        return

    AuditLog.objects.create(
        user=getattr(instance, '_audit_user', None),
        model_name=sender.__name__,
        object_id=str(instance.pk),
        action='create' if created else 'update',
        old_data=getattr(instance, '_old_data', None),
        new_data=model_to_dict(instance),
    )

@receiver(pre_delete)
def delete_audit_log(sender, instance, **kwargs):
    if sender.__name__ not in TRACKED_MODELS:
        return

    AuditLog.objects.create(
        user=getattr(instance, '_audit_user', None),
        model_name=sender.__name__,
        object_id=str(instance.pk),
        action='delete',
        old_data=model_to_dict(instance),
        new_data=None,
    )
