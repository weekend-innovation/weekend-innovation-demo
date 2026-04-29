from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class PushSubscription(models.Model):
    """
    Web Push購読情報。
    ブラウザごとのendpointを保存し、選出通知時に利用する。
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='push_subscriptions',
        verbose_name='ユーザー',
    )
    endpoint = models.URLField(unique=True, verbose_name='Endpoint')
    p256dh = models.TextField(verbose_name='公開鍵(p256dh)')
    auth = models.TextField(verbose_name='認証鍵(auth)')
    user_agent = models.TextField(blank=True, default='', verbose_name='User-Agent')
    is_active = models.BooleanField(default=True, verbose_name='有効')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')

    class Meta:
        verbose_name = 'Push購読'
        verbose_name_plural = 'Push購読'
        indexes = [
            models.Index(fields=['user', 'is_active']),
        ]

    def __str__(self):
        return f"{self.user.username}: {self.endpoint[:40]}"
