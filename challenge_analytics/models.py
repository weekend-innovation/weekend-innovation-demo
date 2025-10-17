"""
課題分析・まとめ機能のモデル
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from challenges.models import Challenge

User = get_user_model()


class ChallengeAnalysis(models.Model):
    """課題分析結果モデル"""
    
    ANALYSIS_STATUS_CHOICES = [
        ('pending', '分析待ち'),
        ('processing', '分析中'),
        ('completed', '完了'),
        ('failed', '失敗'),
    ]
    
    challenge = models.OneToOneField(
        Challenge,
        on_delete=models.CASCADE,
        related_name='analysis',
        verbose_name='課題'
    )
    
    status = models.CharField(
        max_length=20,
        choices=ANALYSIS_STATUS_CHOICES,
        default='pending',
        verbose_name='分析ステータス'
    )
    
    # 分析結果データ
    total_proposals = models.PositiveIntegerField(
        default=0,
        verbose_name='総提案数'
    )
    
    unique_proposers = models.PositiveIntegerField(
        default=0,
        verbose_name='提案者数'
    )
    
    # 提案の内容分析
    common_themes = models.JSONField(
        default=list,
        verbose_name='共通テーマ'
    )
    
    innovative_solutions = models.JSONField(
        default=list,
        verbose_name='革新的解決案'
    )
    
    feasibility_analysis = models.JSONField(
        default=dict,
        verbose_name='実現可能性分析'
    )
    
    # まとめ文
    executive_summary = models.TextField(
        blank=True,
        verbose_name='エグゼクティブサマリー'
    )
    
    detailed_analysis = models.TextField(
        blank=True,
        verbose_name='詳細分析'
    )
    
    recommendations = models.TextField(
        blank=True,
        verbose_name='推奨事項'
    )
    
    # メタデータ
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='作成日時'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='更新日時'
    )
    
    analyzed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='分析完了日時'
    )
    
    class Meta:
        verbose_name = '課題分析'
        verbose_name_plural = '課題分析一覧'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.challenge.title} - {self.get_status_display()}"
    
    def mark_as_completed(self):
        """分析完了としてマーク"""
        self.status = 'completed'
        self.analyzed_at = timezone.now()
        self.save()
    
    def mark_as_failed(self):
        """分析失敗としてマーク"""
        self.status = 'failed'
        self.save()


class ProposalInsight(models.Model):
    """提案の洞察・分析データ"""
    
    analysis = models.ForeignKey(
        ChallengeAnalysis,
        on_delete=models.CASCADE,
        related_name='insights',
        verbose_name='分析'
    )
    
    proposal_id = models.PositiveIntegerField(
        verbose_name='提案ID'
    )
    
    # 洞察データ
    innovation_score = models.FloatField(
        default=0.0,
        verbose_name='革新性スコア'
    )
    
    insightfulness_score = models.FloatField(
        default=0.5,
        verbose_name='支持率スコア'
    )
    
    feasibility_score = models.FloatField(
        default=0.0,
        verbose_name='実現可能性スコア（非推奨）'
    )
    
    impact_score = models.FloatField(
        default=0.0,
        verbose_name='影響度スコア'
    )
    
    key_themes = models.JSONField(
        default=list,
        verbose_name='主要テーマ'
    )
    
    strengths = models.JSONField(
        default=list,
        verbose_name='強み'
    )
    
    concerns = models.JSONField(
        default=list,
        verbose_name='懸念点'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='作成日時'
    )
    
    class Meta:
        verbose_name = '提案洞察'
        verbose_name_plural = '提案洞察一覧'
        unique_together = ['analysis', 'proposal_id']
        ordering = ['-innovation_score', '-feasibility_score']
    
    def __str__(self):
        return f"提案{self.proposal_id}の洞察 - {self.analysis.challenge.title}"