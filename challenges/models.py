from django.db import models
from django.contrib.auth import get_user_model

# カスタムユーザーモデルを取得
User = get_user_model()

class Challenge(models.Model):
    """
    課題モデル
    投稿者が課題を投稿し、提案者が解決案を提案するための課題情報を管理
    """
    STATUS_CHOICES = [
        ('open', '募集中'),
        ('closed', '締切'),
        ('completed', '完了'),
    ]
    
    # 基本情報
    title = models.CharField(max_length=200, verbose_name="課題タイトル")
    description = models.TextField(verbose_name="課題内容")
    contributor = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='contributed_challenges',
        verbose_name="投稿者"
    )
    
    # 報酬・選出情報
    reward_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="提案報酬"
    )
    adoption_reward = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="採用報酬"
    )
    required_participants = models.IntegerField(verbose_name="選出人数")
    
    # 期限・ステータス
    deadline = models.DateTimeField(verbose_name="期限")
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='open',
        verbose_name="ステータス"
    )
    
    # システム情報
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "課題"
        verbose_name_plural = "課題一覧"
    
    def __str__(self):
        return f"{self.title} - {self.contributor.username}"
    
    @property
    def is_open(self):
        """課題が募集中かどうかを判定"""
        return self.status == 'open'
    
    @property
    def is_closed(self):
        """課題が締切かどうかを判定"""
        return self.status == 'closed'
    
    @property
    def is_completed(self):
        """課題が完了かどうかを判定"""
        return self.status == 'completed'