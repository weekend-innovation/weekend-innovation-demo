"""
選出機能のモデル定義
課題に対する提案者の選出を管理
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()

class Selection(models.Model):
    """
    選出モデル
    課題に対する提案者の選出を管理
    """
    STATUS_CHOICES = [
        ('pending', '選出中'),
        ('completed', '選出完了'),
        ('cancelled', 'キャンセル'),
    ]
    
    challenge = models.ForeignKey(
        'challenges.Challenge',
        on_delete=models.CASCADE,
        related_name='selections',
        verbose_name="課題"
    )
    contributor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_selections',
        verbose_name="投稿者"
    )
    selected_users = models.ManyToManyField(
        User,
        related_name='selections',
        blank=True,
        verbose_name="選出されたユーザー"
    )
    required_count = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        verbose_name="選出人数"
    )
    selected_count = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="実際の選出人数"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="ステータス"
    )
    selection_method = models.CharField(
        max_length=50,
        default='random',
        verbose_name="選出方法"
    )
    selection_criteria = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="選出基準"
    )
    notification_sent = models.BooleanField(
        default=False,
        verbose_name="通知送信済み"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="完了日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "選出"
        verbose_name_plural = "選出"
    
    def __str__(self):
        return f"{self.challenge.title} - {self.selected_count}/{self.required_count}人選出"
    
    @property
    def is_completed(self):
        """選出が完了しているかどうか"""
        return self.selected_count >= self.required_count
    
    @property
    def remaining_count(self):
        """残りの選出人数"""
        return max(0, self.required_count - self.selected_count)


class SelectionHistory(models.Model):
    """
    選出履歴モデル
    選出の詳細な履歴を管理
    """
    selection = models.ForeignKey(
        Selection,
        on_delete=models.CASCADE,
        related_name='history',
        verbose_name="選出"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='selection_history',
        verbose_name="ユーザー"
    )
    action = models.CharField(
        max_length=50,
        choices=[
            ('selected', '選出'),
            ('removed', '除外'),
            ('replaced', '代替'),
        ],
        verbose_name="アクション"
    )
    reason = models.TextField(
        blank=True,
        verbose_name="理由"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="メタデータ"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "選出履歴"
        verbose_name_plural = "選出履歴"
    
    def __str__(self):
        return f"{self.selection.challenge.title} - {self.user.username} - {self.action}"


class SelectionCriteria(models.Model):
    """
    選出基準モデル
    選出時の条件やフィルターを管理
    """
    name = models.CharField(max_length=100, verbose_name="基準名")
    description = models.TextField(blank=True, verbose_name="説明")
    criteria_type = models.CharField(
        max_length=50,
        choices=[
            ('random', 'ランダム'),
            ('rating', '評価基準'),
            ('experience', '経験値'),
            ('location', '地域'),
            ('availability', '利用可能時間'),
            ('custom', 'カスタム'),
        ],
        verbose_name="基準タイプ"
    )
    parameters = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="パラメータ"
    )
    is_active = models.BooleanField(default=True, verbose_name="有効")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")
    
    class Meta:
        ordering = ['name']
        verbose_name = "選出基準"
        verbose_name_plural = "選出基準"
    
    def __str__(self):
        return f"{self.name} ({self.criteria_type})"


class ChallengeUserAnonymousName(models.Model):
    """
    課題ごとのユーザー匿名名モデル
    課題内でのユーザーの匿名化された名前を管理
    """
    challenge = models.ForeignKey(
        'challenges.Challenge',
        on_delete=models.CASCADE,
        related_name='user_anonymous_names',
        verbose_name="課題"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='challenge_anonymous_names',
        verbose_name="ユーザー"
    )
    anonymous_name = models.ForeignKey(
        'proposals.AnonymousName',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="匿名名"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")
    
    class Meta:
        unique_together = ['challenge', 'user']
        ordering = ['-created_at']
        verbose_name = "課題ユーザー匿名名"
        verbose_name_plural = "課題ユーザー匿名名"
        indexes = [
            models.Index(fields=['challenge', 'user']),
        ]
    
    def __str__(self):
        anonymous_name_str = self.anonymous_name.name if self.anonymous_name else 'None'
        return f"{self.challenge.title} - {self.user.username} - {anonymous_name_str}"