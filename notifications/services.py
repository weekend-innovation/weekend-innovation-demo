import json
import logging
import os
from typing import Dict

from pywebpush import webpush, WebPushException

from .models import PushSubscription

logger = logging.getLogger(__name__)


class PushNotificationService:
    @staticmethod
    def _vapid_config() -> Dict[str, str] | None:
        public_key = os.getenv('VAPID_PUBLIC_KEY', '').strip()
        private_key = os.getenv('VAPID_PRIVATE_KEY', '').strip()
        subject = os.getenv('VAPID_CLAIMS_SUB', '').strip()
        if not (public_key and private_key and subject):
            return None
        return {
            'public_key': public_key,
            'private_key': private_key,
            'subject': subject,
        }

    @staticmethod
    def send_to_user(user, title: str, body: str, url: str) -> int:
        cfg = PushNotificationService._vapid_config()
        if not cfg:
            logger.info('Push通知スキップ: VAPID設定なし')
            return 0

        sent = 0
        payload = json.dumps({
            'title': title,
            'body': body,
            'url': url,
        })
        subscriptions = PushSubscription.objects.filter(user=user, is_active=True)
        for sub in subscriptions:
            try:
                webpush(
                    subscription_info={
                        'endpoint': sub.endpoint,
                        'keys': {'p256dh': sub.p256dh, 'auth': sub.auth},
                    },
                    data=payload,
                    vapid_private_key=cfg['private_key'],
                    vapid_claims={'sub': cfg['subject']},
                    ttl=86400,
                    timeout=10,
                )
                sent += 1
            except WebPushException as exc:
                status_code = getattr(getattr(exc, 'response', None), 'status_code', None)
                logger.warning("Push送信失敗 user=%s endpoint=%s status=%s", user.username, sub.id, status_code)
                if status_code in (404, 410):
                    sub.is_active = False
                    sub.save(update_fields=['is_active', 'updated_at'])
            except Exception as exc:
                logger.warning("Push送信例外 user=%s endpoint=%s err=%s", user.username, sub.id, exc)
        return sent
