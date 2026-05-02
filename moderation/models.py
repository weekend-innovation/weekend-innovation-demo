"""
モデレーション管理モデル
"""
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone


class Report(models.Model):
    """報告モデル"""
    
    # 報告理由の選択肢
    REASON_CHOICES = [
        ('spam', 'スパム'),
        ('harassment', 'ハラスメント'),
        ('inappropriate_content', '不適切なコンテンツ'),
        ('violence', '暴力的な内容'),
        ('hate_speech', 'ヘイトスピーチ'),
        ('copyright', '著作権侵害'),
        ('fake_news', 'フェイクニュース'),
        ('other', 'その他'),
    ]
    
    # 報告ステータスの選択肢
    STATUS_CHOICES = [
        ('pending', '審査待ち'),
        ('under_review', '審査中'),
        ('resolved', '解決済み'),
        ('dismissed', '却下'),
    ]
    
    # 基本情報
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reports_made',
        verbose_name='報告者'
    )
    
    # 汎用外部キーで報告対象を指定（提案、コメント、ユーザーなど）
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # 報告内容
    reason = models.CharField(
        max_length=50,
        choices=REASON_CHOICES,
        verbose_name='報告理由'
    )
    description = models.TextField(
        blank=True,
        verbose_name='詳細説明'
    )
    
    # ステータス管理
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='ステータス'
    )
    
    # モデレーター情報
    moderator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports_moderated',
        verbose_name='担当モデレーター'
    )
    
    # 審査結果
    moderator_notes = models.TextField(
        blank=True,
        verbose_name='モデレーター備考'
    )
    
    # タイムスタンプ
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='報告日時'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='更新日時'
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='解決日時'
    )
    
    class Meta:
        verbose_name = '報告'
        verbose_name_plural = '報告一覧'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        try:
            target = self.content_object
            label = str(target) if target is not None else "（削除済み参照）"
        except Exception:
            label = "（参照エラー）"
        return f"{self.reporter.username} -> {label} ({self.reason})"
    
    def get_content_type_name(self):
        """コンテンツタイプの表示名を取得"""
        if self.content_type.model == 'proposal':
            return '提案'
        elif self.content_type.model == 'proposalcomment':
            return 'コメント'
        elif self.content_type.model == 'user':
            return 'ユーザー'
        else:
            return self.content_type.model


class UserSuspension(models.Model):
    """ユーザー利用停止モデル"""
    
    # 停止理由の選択肢
    SUSPENSION_REASON_CHOICES = [
        ('spam', 'スパム行為'),
        ('harassment', 'ハラスメント'),
        ('inappropriate_content', '不適切なコンテンツ'),
        ('violence', '暴力的な内容'),
        ('hate_speech', 'ヘイトスピーチ'),
        ('copyright', '著作権侵害'),
        ('fake_news', 'フェイクニュース'),
        ('multiple_violations', '複数回の違反'),
        ('other', 'その他'),
    ]
    
    # 停止ステータスの選択肢
    STATUS_CHOICES = [
        ('active', '停止中'),
        ('expired', '期限切れ'),
        ('lifted', '解除済み'),
    ]
    
    # 基本情報
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='suspensions',
        verbose_name='対象ユーザー'
    )
    
    # 停止情報
    reason = models.CharField(
        max_length=50,
        choices=SUSPENSION_REASON_CHOICES,
        verbose_name='停止理由'
    )
    description = models.TextField(
        verbose_name='停止理由詳細'
    )
    
    # 停止期間
    suspended_from = models.DateTimeField(
        default=timezone.now,
        verbose_name='停止開始日時'
    )
    suspended_until = models.DateTimeField(
        verbose_name='停止終了日時'
    )
    
    # ステータス
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='ステータス'
    )
    
    # モデレーター情報
    moderator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='suspensions_given',
        verbose_name='実行モデレーター'
    )
    
    # 関連報告
    related_reports = models.ManyToManyField(
        Report,
        blank=True,
        verbose_name='関連報告'
    )
    
    # タイムスタンプ
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='作成日時'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='更新日時'
    )
    lifted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='解除日時'
    )
    
    class Meta:
        verbose_name = 'ユーザー利用停止'
        verbose_name_plural = 'ユーザー利用停止一覧'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['status']),
            models.Index(fields=['suspended_until']),
        ]
    
    def __str__(self):
        return f'{self.user.username} - {self.reason} ({self.suspended_until})'
    
    @property
    def is_active(self):
        """停止が有効かどうか"""
        if self.status != 'active':
            return False
        return timezone.now() < self.suspended_until
    
    @property
    def days_remaining(self):
        """残り停止日数"""
        if not self.is_active:
            return 0
        delta = self.suspended_until - timezone.now()
        return max(0, delta.days)


class ModerationAction(models.Model):
    """モデレーションアクション履歴"""
    
    # アクションタイプの選択肢
    ACTION_CHOICES = [
        ('report_created', '報告作成'),
        ('report_reviewed', '報告審査'),
        ('report_resolved', '報告解決'),
        ('user_suspended', 'ユーザー停止'),
        ('user_unsuspended', 'ユーザー停止解除'),
        ('user_deleted', 'ユーザー削除'),
        ('content_hidden', 'コンテンツ非表示'),
        ('content_deleted', 'コンテンツ削除'),
    ]
    
    # 基本情報
    moderator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderation_actions',
        verbose_name='実行者'
    )
    
    action_type = models.CharField(
        max_length=30,
        choices=ACTION_CHOICES,
        verbose_name='アクションタイプ'
    )
    
    # 対象情報
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='actions_against',
        verbose_name='対象ユーザー'
    )
    
    # 汎用外部キーで対象コンテンツを指定
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # アクション詳細
    description = models.TextField(
        verbose_name='アクション詳細'
    )
    
    # タイムスタンプ
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='実行日時'
    )
    
    class Meta:
        verbose_name = 'モデレーションアクション'
        verbose_name_plural = 'モデレーションアクション履歴'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['action_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        tu = self.target_user.username if self.target_user_id and self.target_user else "(ユーザー削除済)"
        return f"{self.action_type} - {tu} ({self.created_at})"