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
        if self.is_anonymous and self.anonymous_name:
            return f"{self.title} (by {self.anonymous_name.name})"
        return f"{self.title} (by {self.proposer.username})"
    
    def get_display_name(self, request_user=None):
        """表示用の名前を返す"""
        # リクエストユーザーが提案者本人の場合は実名を返す
        if request_user and request_user == self.proposer:
            return self.proposer.username
        
        # それ以外の場合は匿名名を返す（匿名化されている場合）
        if self.is_anonymous and self.anonymous_name:
            return self.anonymous_name.name
        return self.proposer.username