from django.urls import path
from .views import UserEventListView

urlpatterns = [
    path('me/', UserEventListView.as_view(), name='user-events-list'),
]
