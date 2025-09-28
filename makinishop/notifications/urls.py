from django.urls import path
from .views import (
    NotificationTemplateListView, NotificationTemplateCreateView,
    UserNotificationPrefListCreateView, UserNotificationPrefDetailView,
    NotificationQueueListView, TriggerNotificationView
)

urlpatterns = [
    # Templates
    path('templates/', NotificationTemplateListView.as_view(), name='notification-template-list'),
    path('templates/create/', NotificationTemplateCreateView.as_view(), name='notification-template-create'),

    # User Preferences
    path('preferences/', UserNotificationPrefListCreateView.as_view(), name='notification-pref-list-create'),
    path('preferences/<int:pk>/', UserNotificationPrefDetailView.as_view(), name='notification-pref-detail'),

    # Queue (admin/debug)
    path('queue/', NotificationQueueListView.as_view(), name='notification-queue-list'),

    # Trigger notification
    path('trigger/', TriggerNotificationView.as_view(), name='notification-trigger'),
]
