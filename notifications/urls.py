from django.urls import path

from .views import PushSubscribeView, PushUnsubscribeView

urlpatterns = [
    path('push/subscribe/', PushSubscribeView.as_view(), name='push-subscribe'),
    path('push/unsubscribe/', PushUnsubscribeView.as_view(), name='push-unsubscribe'),
]
