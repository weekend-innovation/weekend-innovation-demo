from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PushSubscription
from .serializers import PushSubscribeSerializer, PushUnsubscribeSerializer


class PushSubscribeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PushSubscribeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        sub, _ = PushSubscription.objects.update_or_create(
            endpoint=data['endpoint'],
            defaults={
                'user': request.user,
                'p256dh': data['p256dh'],
                'auth': data['auth'],
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'is_active': True,
            },
        )
        return Response(
            {'id': sub.id, 'status': 'subscribed'},
            status=status.HTTP_200_OK,
        )


class PushUnsubscribeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PushUnsubscribeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        endpoint = serializer.validated_data['endpoint']
        deleted, _ = PushSubscription.objects.filter(
            user=request.user,
            endpoint=endpoint,
        ).delete()
        return Response(
            {'status': 'unsubscribed', 'deleted': deleted},
            status=status.HTTP_200_OK,
        )
