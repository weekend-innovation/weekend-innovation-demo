from django.db import models
from django.contrib.auth import get_user_model

# カスタムユーザーモデルを取得
User = get_user_model()

class Proposal(models.Model):
    """
    提案モデル
    提案者が課題に対する解決案を提案するためのモデル
    結論と理由を分離して管理
    """
    challenge = models.ForeignKey(
        'challenges.Challenge', 
        on_delete=models.CASCADE, 
        related_name='proposals',
        verbose_name="課題"
    )
    proposer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='proposals',
        verbose_name="提案者"
    )
    
    # 結論と理由を分離
    conclusion = models.TextField(verbose_name="結論")
    reasoning = models.TextField(verbose_name="理由")
    
    # ステータス管理
    is_adopted = models.BooleanField(default=False, verbose_name="採用フラグ")
    is_deleted = models.BooleanField(default=False, verbose_name="削除フラグ")
    
    # システム情報
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "提案"
        verbose_name_plural = "提案一覧"
        # 同じ課題に対して同じ提案者は1つの提案のみ可能
        unique_together = ['challenge', 'proposer']
    
    def __str__(self):
        return f"{self.challenge.title} - {self.proposer.username}"
    
    @property
    def is_active(self):
        """提案がアクティブかどうかを判定"""
        return not self.is_deleted
    
    @property
    def is_selected(self):
        """提案が選出されているかどうかを判定"""
        return hasattr(self, 'selection') and self.selection is not None

class ProposalComment(models.Model):
    """
    提案コメントモデル
    理由・推論過程のみにコメント可能
    """
    COMMENT_TARGETS = [
        ('reasoning', '理由'),
        ('inference', '推論過程'),
    ]
    
    proposal = models.ForeignKey(
        Proposal, 
        on_delete=models.CASCADE, 
        related_name='comments',
        verbose_name="提案"
    )
    commenter = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='proposal_comments',
        verbose_name="コメント投稿者"
    )
    target_section = models.CharField(
        max_length=20, 
        choices=COMMENT_TARGETS, 
        verbose_name="コメント対象"
    )
    
    # コメントも結論と理由を分離
    conclusion = models.TextField(verbose_name="コメントの結論")
    reasoning = models.TextField(verbose_name="コメントの理由")
    
    # ステータス管理
    is_deleted = models.BooleanField(default=False, verbose_name="削除フラグ")
    
    # システム情報
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    
    class Meta:
        ordering = ['created_at']
        verbose_name = "提案コメント"
        verbose_name_plural = "提案コメント一覧"
    
    def __str__(self):
        return f"{self.proposal.challenge.title} - {self.commenter.username}のコメント"
    
    @property
    def is_active(self):
        """コメントがアクティブかどうかを判定"""
        return not self.is_deleted

class ProposalEvaluation(models.Model):
    """
    提案評価モデル
    提案に対する「思い付いたか」の評価
    """
    EVALUATION_CHOICES = [
        ('yes', 'Yes'),
        ('maybe', 'Maybe'),
        ('no', 'No'),
    ]
    
    proposal = models.ForeignKey(
        Proposal, 
        on_delete=models.CASCADE, 
        related_name='evaluations',
        verbose_name="提案"
    )
    evaluator = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='proposal_evaluations',
        verbose_name="評価者"
    )
    evaluation = models.CharField(
        max_length=10, 
        choices=EVALUATION_CHOICES, 
        verbose_name="評価"
    )
    
    # システム情報
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "提案評価"
        verbose_name_plural = "提案評価一覧"
        # 同じ提案に対して同じ評価者は1つの評価のみ可能
        unique_together = ['proposal', 'evaluator']
    
    def __str__(self):
        return f"{self.proposal.challenge.title} - {self.evaluator.username}: {self.evaluation}"
    
    @property
    def evaluation_display(self):
        """評価の表示名を取得"""
        return dict(self.EVALUATION_CHOICES)[self.evaluation]