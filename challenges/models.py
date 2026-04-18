import math
from django.db import models
from django.contrib.auth import get_user_model
from datetime import timedelta
from django.core.exceptions import ValidationError

# カスタムユーザーモデルを取得
User = get_user_model()

# 各フェーズの最低日数（提案3日、編集1日、評価2日）→ 合計6日以上必要
MIN_PROPOSAL_DAYS = 3
MIN_EDIT_DAYS = 1
MIN_EVALUATION_DAYS = 2
MIN_TOTAL_DAYS = MIN_PROPOSAL_DAYS + MIN_EDIT_DAYS + MIN_EVALUATION_DAYS  # 6

def calculate_phase_deadlines(start_datetime, total_days):
    """
    総期限日数から3つの期限を計算（案A: 提案50%, 編集20%, 評価30%）
    重要度順に切り上げ、編集期間で帳尻合わせ（一意に決まる）
    最低: 提案3日、編集1日、評価2日（total_days >= 6 であること）
    
    Args:
        start_datetime: 開始日時
        total_days: 総日数
    
    Returns:
        tuple: (proposal_deadline, edit_deadline, evaluation_deadline)
    
    Raises:
        ValueError: total_days < 6 の場合
    """
    if total_days < MIN_TOTAL_DAYS:
        raise ValueError(
            f"期限まで最低{MIN_TOTAL_DAYS}日必要です"
            f"（提案{MIN_PROPOSAL_DAYS}日、編集{MIN_EDIT_DAYS}日、評価{MIN_EVALUATION_DAYS}日）"
        )
    
    # 案1: 重要度順に切り上げ、編集で調整
    proposal_days = math.ceil(total_days * 0.5)   # 提案 50%
    edit_days = math.ceil(total_days * 0.2)       # 編集 20%
    evaluation_days = total_days - proposal_days - edit_days  # 評価 = 残り
    
    # 評価期間が最低2日未満の場合、編集・提案から調整
    if evaluation_days < MIN_EVALUATION_DAYS:
        need = MIN_EVALUATION_DAYS - evaluation_days
        if edit_days - need >= MIN_EDIT_DAYS:
            edit_days -= need
            evaluation_days = MIN_EVALUATION_DAYS
        else:
            give_from_edit = edit_days - MIN_EDIT_DAYS
            edit_days = MIN_EDIT_DAYS
            evaluation_days += give_from_edit
            if evaluation_days < MIN_EVALUATION_DAYS:
                proposal_days -= (MIN_EVALUATION_DAYS - evaluation_days)
                evaluation_days = MIN_EVALUATION_DAYS
    
    # 各期限を計算（その日の23:59:59まで）
    proposal_deadline = start_datetime + timedelta(days=proposal_days)
    proposal_deadline = proposal_deadline.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    edit_deadline = start_datetime + timedelta(days=proposal_days + edit_days)
    edit_deadline = edit_deadline.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    evaluation_deadline = start_datetime + timedelta(days=proposal_days + edit_days + evaluation_days)
    evaluation_deadline = evaluation_deadline.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    return proposal_deadline, edit_deadline, evaluation_deadline

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
    deadline = models.DateTimeField(verbose_name="期限（全体）")  # 総期限（後方互換性のため残す）
    proposal_deadline = models.DateTimeField(verbose_name="提案期限", null=True, blank=True)
    edit_deadline = models.DateTimeField(verbose_name="編集期限", null=True, blank=True)
    evaluation_deadline = models.DateTimeField(verbose_name="評価期限", null=True, blank=True)
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

    def clean(self):
        """
        期限の整合性をモデル層で保証する。
        API経由以外（管理コマンド等）でも不整合データを防ぐための最終防衛線。
        """
        errors = {}

        phase_deadlines = [self.proposal_deadline, self.edit_deadline, self.evaluation_deadline]
        has_any_phase_deadline = any(d is not None for d in phase_deadlines)
        has_all_phase_deadlines = all(d is not None for d in phase_deadlines)

        if has_any_phase_deadline and not has_all_phase_deadlines:
            errors['deadline'] = "提案期限・編集期限・評価期限はすべて設定する必要があります。"

        if has_all_phase_deadlines:
            if self.proposal_deadline > self.edit_deadline:
                errors['proposal_deadline'] = "提案期限は編集期限以前である必要があります。"
            if self.edit_deadline > self.evaluation_deadline:
                errors['edit_deadline'] = "編集期限は評価期限以前である必要があります。"

            if self.created_at and self.created_at > self.proposal_deadline:
                errors['proposal_deadline'] = "提案期限は作成日時より後である必要があります。"

            # status 更新判定と表示判定のズレを防ぐため、全体期限は評価期限と一致させる
            if self.deadline and self.deadline != self.evaluation_deadline:
                errors['deadline'] = "全体期限は評価期限と一致する必要があります。"

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
    
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
    
    def get_current_phase(self):
        """
        現在の課題フェーズを判定
        返り値: 'proposal', 'edit', 'evaluation', 'closed'
        """
        from django.utils import timezone
        now = timezone.now()
        
        # 新しい期限フィールドがない場合は従来のロジック
        if not self.proposal_deadline or not self.edit_deadline or not self.evaluation_deadline:
            return 'closed' if self.status == 'closed' else 'proposal'
        
        # 提案期間中
        if now <= self.proposal_deadline:
            return 'proposal'
        # 編集期間中
        elif now <= self.edit_deadline:
            return 'edit'
        # 評価期間中
        elif now <= self.evaluation_deadline:
            return 'evaluation'
        # 期限切れ
        else:
            return 'closed'
    
    @property
    def current_phase(self):
        """現在のフェーズをプロパティとして取得"""
        return self.get_current_phase()
    
    @property
    def phase_display(self):
        """フェーズの日本語表示"""
        phase = self.get_current_phase()
        phase_map = {
            'proposal': '提案期間中',
            'edit': '編集期間中',
            'evaluation': '評価期間中',
            'closed': '期限切れ'
        }
        return phase_map.get(phase, '不明')
    
    def has_user_proposed(self, user):
        """
        指定されたユーザーがこの課題に提案しているかチェック
        
        Args:
            user: チェック対象のユーザー
            
        Returns:
            bool: 提案している場合True
        """
        from proposals.models import Proposal
        return Proposal.objects.filter(challenge=self, proposer=user).exists()
    
    def get_priority_for_proposer(self, user):
        """
        提案者用の優先度を計算
        
        Args:
            user: 提案者ユーザー
            
        Returns:
            int: 優先度（小さいほど高優先度）
        """
        from selections.models import UserEvaluationCompletion
        
        phase = self.get_current_phase()
        has_proposed = self.has_user_proposed(user)
        
        # 提案していない場合、提案期間以外は全て期限切れ扱い
        if not has_proposed and phase != 'proposal':
            return 5  # 期限切れ（未提案）
        
        # 評価完了状態をチェック
        has_completed_evaluations = False
        if phase == 'evaluation':
            try:
                completion = UserEvaluationCompletion.objects.get(
                    challenge=self,
                    user=user
                )
                has_completed_evaluations = completion.has_completed_all_evaluations
            except UserEvaluationCompletion.DoesNotExist:
                has_completed_evaluations = False
        
        # 優先度を決定
        if phase == 'proposal' and not has_proposed:
            return 1  # 最優先：提案期間中で未提案
        elif phase == 'edit':
            return 2  # 編集期間中（提案済み）
        elif phase == 'evaluation' and not has_completed_evaluations:
            return 3  # 評価期間中で評価未完了（提案済み）
        elif phase == 'evaluation' and has_completed_evaluations:
            return 4  # 評価期間中で評価完了（提案済み）
        elif phase == 'closed':
            return 5  # 期限切れ
        else:
            return 6  # その他