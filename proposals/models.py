from django.db import models
from django.conf import settings

class AnonymousName(models.Model):
    """
    匿名化用の名前モデル
    動物、植物、無機物の名前を管理
    """
    CATEGORY_CHOICES = [
        ('animal', 'Animal'),
        ('plant', 'Plant'),
        ('inorganic', 'Inorganic'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Anonymous Name'
        verbose_name_plural = 'Anonymous Names'
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"

class Proposal(models.Model):
    """
    提案モデル
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('adopted', 'Adopted'),
        ('rejected', 'Rejected'),
    ]
    
    # 基本情報
    conclusion = models.TextField(default='')
    reasoning = models.TextField(default='')
    
    # 関連情報
    challenge = models.ForeignKey('challenges.Challenge', on_delete=models.CASCADE, related_name='proposals')
    proposer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='proposals')
    
    # 匿名化関連
    anonymous_name = models.ForeignKey(AnonymousName, on_delete=models.SET_NULL, null=True, blank=True)
    is_anonymous = models.BooleanField(default=True)
    
    # ステータス
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    is_adopted = models.BooleanField(default=False)
    
    # 評価関連
    rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    rating_count = models.IntegerField(default=0)
    
    # タイムスタンプ
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Proposal'
        verbose_name_plural = 'Proposals'
    
    def __str__(self):
        text = (self.conclusion or '').strip()
        excerpt = text[:60] + ('…' if len(text) > 60 else '') if text else f'#{self.pk}'
        author = (
            self.anonymous_name.name
            if self.is_anonymous and self.anonymous_name
            else self.proposer.username
        )
        return f'{excerpt} (by {author})'
    
    def get_display_name(self, request_user=None):
        """表示用の名前を返す"""
        # リクエストユーザーが提案者本人の場合は実名を返す
        if request_user and request_user == self.proposer:
            return self.proposer.username
        
        # それ以外の場合は匿名名を返す（匿名化されている場合）
        if self.is_anonymous and self.anonymous_name:
            return self.anonymous_name.name
        return self.proposer.username


class ProposalComment(models.Model):
    """
    提案コメントモデル
    理由・推論過程へのコメントのみ許可
    """
    COMMENT_TARGETS = [
        ('reasoning', '理由'),
        ('inference', '推論過程'),
    ]
    
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name='comments')
    commenter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='proposal_comments')
    target_section = models.CharField(max_length=20, choices=COMMENT_TARGETS, verbose_name="コメント対象")
    conclusion = models.TextField(verbose_name="コメントの結論")
    reasoning = models.TextField(verbose_name="コメントの理由")
    is_deleted = models.BooleanField(default=False, verbose_name="削除フラグ")
    is_read = models.BooleanField(default=False, verbose_name="既読フラグ")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Proposal Comment'
        verbose_name_plural = 'Proposal Comments'
    
    def __str__(self):
        return f"Comment on {self.proposal.id} - {self.target_section}"


class ProposalEvaluation(models.Model):
    """
    提案評価モデル
    同じく選出された提案者のみが評価可能
    """
    EVALUATION_CHOICES = [
        ('yes', 'Yes'),
        ('maybe', 'Maybe'),
        ('no', 'No'),
    ]
    
    INSIGHT_CHOICES = [
        ('5', '5'),
        ('4', '4'),
        ('3', '3'),
        ('2', '2'),
        ('1', '1'),
    ]
    
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name='evaluations')
    evaluator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='proposal_evaluations')
    
    # 革新性評価
    evaluation = models.CharField(max_length=10, choices=EVALUATION_CHOICES, verbose_name="革新性評価")
    score = models.IntegerField(verbose_name="革新性点数", default=0)  # No=2, Maybe=1, Yes=0
    
    # 示唆性評価（新規）
    insight_level = models.CharField(max_length=1, choices=INSIGHT_CHOICES, verbose_name="示唆性評価", null=True, blank=True)
    insight_score = models.IntegerField(verbose_name="示唆性点数", default=3, null=True, blank=True)  # 1-5
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['proposal', 'evaluator']
        verbose_name = 'Proposal Evaluation'
        verbose_name_plural = 'Proposal Evaluations'
    
    def save(self, *args, **kwargs):
        # 革新性評価に応じて点数を自動設定
        if self.evaluation == 'no':
            self.score = 2
        elif self.evaluation == 'maybe':
            self.score = 1
        elif self.evaluation == 'yes':
            self.score = 0
        
        # 示唆性評価に応じて点数を自動設定
        if self.insight_level:
            self.insight_score = int(self.insight_level)
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Evaluation {self.evaluation} on Proposal {self.proposal.id}"


class ProposalCommentReply(models.Model):
    """
    コメント返信モデル
    提案者のみが返信可能
    """
    comment = models.ForeignKey(ProposalComment, on_delete=models.CASCADE, related_name='replies')
    replier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='proposal_comment_replies')
    content = models.TextField(verbose_name="返信内容")
    is_deleted = models.BooleanField(default=False, verbose_name="削除フラグ")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Proposal Comment Reply'
        verbose_name_plural = 'Proposal Comment Replies'
    
    def __str__(self):
        return f"Reply to Comment {self.comment.id}"


class ProposalEditReference(models.Model):
    """
    解決案編集時のコメント参考ログ
    提案者が「参考」ボタンで特定のコメントを参考に編集した記録（支持率の算出に使用）
    """
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name='edit_references')
    comment = models.ForeignKey('ProposalComment', on_delete=models.CASCADE, related_name='edit_references')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '解決案編集参考'
        verbose_name_plural = '解決案編集参考'
        unique_together = ['proposal', 'comment']

    def __str__(self):
        return f"Proposal {self.proposal.id} edited referencing Comment {self.comment.id}"


class ProposalReference(models.Model):
    """
    提案参考モデル
    回答編集権限を持つユーザーが参考として保存
    """
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name='references')
    referencer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='proposal_references')
    notes = models.TextField(blank=True, verbose_name="参考メモ")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['proposal', 'referencer']
        verbose_name = 'Proposal Reference'
        verbose_name_plural = 'Proposal References'
    
    def __str__(self):
        return f"Reference to Proposal {self.proposal.id}"