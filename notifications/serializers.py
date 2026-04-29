from rest_framework import serializers


class PushSubscribeSerializer(serializers.Serializer):
    endpoint = serializers.URLField()
    keys = serializers.DictField(child=serializers.CharField(), required=True)

    def validate(self, attrs):
        keys = attrs.get('keys') or {}
        p256dh = keys.get('p256dh')
        auth = keys.get('auth')
        if not p256dh or not auth:
            raise serializers.ValidationError('keys.p256dh と keys.auth は必須です。')
        attrs['p256dh'] = p256dh
        attrs['auth'] = auth
        return attrs


class PushUnsubscribeSerializer(serializers.Serializer):
    endpoint = serializers.URLField()
