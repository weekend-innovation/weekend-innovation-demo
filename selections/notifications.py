"""
選出機能の通知システム
選出結果の通知を管理
"""
import logging
from typing import List, Dict, Any
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import get_user_model

from .models import Selection

User = get_user_model()
logger = logging.getLogger(__name__)

_SELECTION_METHOD_LABELS = {
    'random': 'ランダム選出',
    'weighted': '重み付き選出',
}


def _selection_method_label(method: str) -> str:
    return _SELECTION_METHOD_LABELS.get(method, method or '—')


class SelectionNotificationService:
    """
    選出通知サービスクラス
    選出結果の通知を管理
    """
    
    @staticmethod
    def send_selection_notification(selection: Selection) -> bool:
        """
        選出結果の通知を送信
        
        Args:
            selection: 選出オブジェクト
            
        Returns:
            bool: 送信成功フラグ
        """
        try:
            # 選出されたユーザーに通知
            success_count = 0
            total_count = selection.selected_users.count()
            
            for user in selection.selected_users.all():
                if SelectionNotificationService._send_user_notification(selection, user):
                    success_count += 1
            
            # 投稿者に通知
            SelectionNotificationService._send_contributor_notification(selection)
            
            # 通知送信済みフラグを更新
            selection.notification_sent = True
            selection.save()
            
            logger.info(f"選出通知送信完了: {selection.id}, 成功: {success_count}/{total_count}")
            return True
            
        except Exception as e:
            logger.error(f"選出通知送信エラー: {e}")
            return False
    
    @staticmethod
    def _send_user_notification(selection: Selection, user: User) -> bool:
        """
        選出されたユーザーに通知を送信
        
        Args:
            selection: 選出オブジェクト
            user: 対象ユーザー
            
        Returns:
            bool: 送信成功フラグ
        """
        try:
            # メール通知
            if user.email:
                SelectionNotificationService._send_email_notification(
                    selection, user, 'selected'
                )
            
            # システム内通知（今後の実装用）
            SelectionNotificationService._create_system_notification(
                selection, user, 'selected'
            )
            
            logger.info(f"ユーザー通知送信成功: {user.username}")
            return True
            
        except Exception as e:
            logger.error(f"ユーザー通知送信エラー (user: {user.username}): {e}")
            return False
    
    @staticmethod
    def _send_contributor_notification(selection: Selection) -> bool:
        """
        投稿者に通知を送信
        
        Args:
            selection: 選出オブジェクト
            
        Returns:
            bool: 送信成功フラグ
        """
        try:
            contributor = selection.contributor
            
            # メール通知
            if contributor.email:
                SelectionNotificationService._send_email_notification(
                    selection, contributor, 'contributor'
                )
            
            # システム内通知
            SelectionNotificationService._create_system_notification(
                selection, contributor, 'contributor'
            )
            
            logger.info(f"投稿者通知送信成功: {contributor.username}")
            return True
            
        except Exception as e:
            logger.error(f"投稿者通知送信エラー: {e}")
            return False
    
    @staticmethod
    def _send_email_notification(selection: Selection, user: User, notification_type: str) -> bool:
        """
        メール通知を送信
        
        Args:
            selection: 選出オブジェクト
            user: 対象ユーザー
            notification_type: 通知タイプ ('selected', 'contributor')
            
        Returns:
            bool: 送信成功フラグ
        """
        try:
            # メールテンプレートのコンテキスト
            context = {
                'user': user,
                'selection': selection,
                'challenge': selection.challenge,
                'contributor': selection.contributor,
                'site_name': getattr(settings, 'SITE_NAME', 'Weekend Innovation'),
                'site_url': getattr(settings, 'SITE_URL', 'http://localhost:3000'),
                'selection_method_label': _selection_method_label(
                    selection.selection_method
                ),
            }
            
            if notification_type == 'selected':
                # 選出されたユーザー向け
                subject = f'【{context["site_name"]}】課題への選出通知'
                template = 'selections/email/selected_notification.html'
            elif notification_type == 'contributor':
                # 投稿者向け
                subject = f'【{context["site_name"]}】選出完了通知'
                template = 'selections/email/contributor_notification.html'
            else:
                logger.warning(f"未知の通知タイプ: {notification_type}")
                return False
            
            # メール本文を生成
            html_message = render_to_string(template, context)
            plain_message = SelectionNotificationService._generate_plain_message(context, notification_type)
            
            # メール送信
            send_mail(
                subject=subject,
                message=plain_message,
                html_message=html_message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@weekend-innovation.com'),
                recipient_list=[user.email],
                fail_silently=False,
            )
            
            logger.info(f"メール通知送信成功: {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"メール通知送信エラー (user: {user.email}): {e}")
            return False
    
    @staticmethod
    def _generate_plain_message(context: Dict[str, Any], notification_type: str) -> str:
        """
        プレーンテキストメッセージを生成
        
        Args:
            context: テンプレートコンテキスト
            notification_type: 通知タイプ
            
        Returns:
            str: プレーンテキストメッセージ
        """
        user = context['user']
        selection = context['selection']
        challenge = context['challenge']
        site_name = context['site_name']
        site_url = context['site_url']
        
        if notification_type == 'selected':
            return f"""
{user.username} 様

{site_name}へのご登録ありがとうございます。

課題「{challenge.title}」に選出されました！

■ 課題詳細
- タイトル: {challenge.title}
- 投稿者: {selection.contributor.username}
- 選出人数: {selection.selected_count}/{selection.required_count}人
- 提案報酬: ¥{challenge.reward_amount:,}
- 採用報酬: ¥{challenge.adoption_reward:,}
- 期限: {challenge.deadline.strftime('%Y年%m月%d日 %H:%M')}

■ 次のステップ
以下のURLから課題詳細を確認し、解決案を提案してください：
{site_url}/challenges/{challenge.id}/propose

ご質問がございましたら、お気軽にお問い合わせください。

{site_name} 運営チーム
"""
        elif notification_type == 'contributor':
            return f"""
{user.username} 様

課題「{challenge.title}」の選出が完了しました。

■ 選出結果
- 選出人数: {selection.selected_count}/{selection.required_count}人
- 選出方法: {_selection_method_label(selection.selection_method)}
- 完了日時: {selection.completed_at.strftime('%Y年%m月%d日 %H:%M')}

■ 選出されたユーザー
{', '.join([u.username for u in selection.selected_users.all()])}

以下のURLから選出結果の詳細を確認できます：
{site_url}/selections/{selection.id}

ご質問がございましたら、お気軽にお問い合わせください。

{site_name} 運営チーム
"""
        else:
            return "通知メッセージの生成に失敗しました。"
    
    @staticmethod
    def _create_system_notification(selection: Selection, user: User, notification_type: str) -> bool:
        """
        システム内通知を作成（今後の実装用）
        
        Args:
            selection: 選出オブジェクト
            user: 対象ユーザー
            notification_type: 通知タイプ
            
        Returns:
            bool: 作成成功フラグ
        """
        try:
            # 今後の実装でnotificationsアプリと連携
            # 現在はログ出力のみ
            logger.info(f"システム通知作成: {user.username} - {notification_type}")
            return True
            
        except Exception as e:
            logger.error(f"システム通知作成エラー: {e}")
            return False
    
    @staticmethod
    def send_selection_reminder(selection: Selection) -> bool:
        """
        選出リマインダーを送信
        
        Args:
            selection: 選出オブジェクト
            
        Returns:
            bool: 送信成功フラグ
        """
        try:
            # 選出されたユーザーにリマインダーを送信
            for user in selection.selected_users.all():
                if user.email:
                    SelectionNotificationService._send_reminder_email(selection, user)
            
            logger.info(f"選出リマインダー送信完了: {selection.id}")
            return True
            
        except Exception as e:
            logger.error(f"選出リマインダー送信エラー: {e}")
            return False
    
    @staticmethod
    def _send_reminder_email(selection: Selection, user: User) -> bool:
        """
        リマインダーメールを送信
        
        Args:
            selection: 選出オブジェクト
            user: 対象ユーザー
            
        Returns:
            bool: 送信成功フラグ
        """
        try:
            challenge = selection.challenge
            site_name = getattr(settings, 'SITE_NAME', 'Weekend Innovation')
            site_url = getattr(settings, 'SITE_URL', 'http://localhost:3000')
            
            subject = f'【{site_name}】課題提案のリマインダー'
            message = f"""
{user.username} 様

課題「{challenge.title}」への提案期限が近づいています。

■ 課題詳細
- タイトル: {challenge.title}
- 期限: {challenge.deadline.strftime('%Y年%m月%d日 %H:%M')}
- 提案報酬: ¥{challenge.reward_amount:,}

まだ提案を投稿されていない場合は、お早めにご対応ください。

提案ページ: {site_url}/challenges/{challenge.id}/propose

{site_name} 運営チーム
"""
            
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@weekend-innovation.com'),
                recipient_list=[user.email],
                fail_silently=True,
            )
            
            logger.info(f"リマインダーメール送信成功: {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"リマインダーメール送信エラー: {e}")
            return False

