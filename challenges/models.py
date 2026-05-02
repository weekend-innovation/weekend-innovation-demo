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

# 課題の総日数の上限（API・管理画面の目安。長期化による評価負荷・離脱を抑える）
MAX_TOTAL_DAYS = 90

# フェーズ日数の基準比率（提案:編集:評価）＝4:2:3
# 4:2:4 に近い共創・編集の重みを保ちつつ、評価を提案より短くし「提案 > 評価 > 編集」を満たす。
_PHASE_WEIGHTS_SUM = 9
_PHASE_WEIGHT_PROPOSAL = 4
_PHASE_WEIGHT_EDIT = 2
_PHASE_WEIGHT_EVALUATION = 3


def _allocate_phase_days_ratio(total_days: int) -> tuple[int, int, int]:
    """
    提案・編集・評価の日数を整数で割り当てる（合計 total_days）。

    - 基準比率 4:2:3（Hamilton 最大剰余で端数を配分）
    - その後、最低日数と 提案 > 評価 > 編集 を満たすよう微調整
    """
    s = _PHASE_WEIGHTS_SUM
    vals = {
        "p": total_days * _PHASE_WEIGHT_PROPOSAL,
        "ed": total_days * _PHASE_WEIGHT_EDIT,
        "ev": total_days * _PHASE_WEIGHT_EVALUATION,
    }
    seats = {k: vals[k] // s for k in vals}
    r = total_days - sum(seats.values())
    # 端数は「重み×総日数 mod s」が大きい順（同率は提案→評価→編集）
    prio = {"p": 2, "ev": 1, "ed": 0}
    for _ in range(r):
        k = max(vals, key=lambda x: ((vals[x] - seats[x] * s), prio[x]))
        seats[k] += 1

    p, ed, ev = seats["p"], seats["ed"], seats["ev"]

    for _ in range(total_days * 4):
        if p + ed + ev != total_days:
            diff = total_days - (p + ed + ev)
            if diff > 0:
                p += diff
                continue
            if diff < 0:
                if p > MIN_PROPOSAL_DAYS:
                    p += diff
                    continue
                if ev > MIN_EVALUATION_DAYS:
                    ev += diff
                    continue
                if ed > MIN_EDIT_DAYS:
                    ed += diff
                    continue
            break

        if p < MIN_PROPOSAL_DAYS:
            if ev > MIN_EVALUATION_DAYS and ev > ed:
                ev -= 1
                p += 1
                continue
            if ed > MIN_EDIT_DAYS:
                ed -= 1
                p += 1
                continue
            break

        if ev < MIN_EVALUATION_DAYS:
            if p > MIN_PROPOSAL_DAYS and p - 1 > ev:
                p -= 1
                ev += 1
                continue
            if ed > MIN_EDIT_DAYS:
                ed -= 1
                ev += 1
                continue
            break

        if ed < MIN_EDIT_DAYS:
            if ev > MIN_EVALUATION_DAYS and ev - 1 > ed:
                ev -= 1
                ed += 1
                continue
            if p > MIN_PROPOSAL_DAYS:
                p -= 1
                ed += 1
                continue
            break

        if p > ev > ed:
            break

        # 編集と評価が同数などで「評価 > 編集」が崩れるときは、編集から提案へ1日ずらす（例: T=7 の 3,2,2 → 4,1,2）
        if ed >= ev and ed > MIN_EDIT_DAYS and p + 1 > ev:
            p += 1
            ed -= 1
            continue

        if ev >= p:
            if ed > MIN_EDIT_DAYS:
                ed -= 1
                p += 1
                continue
            if ev > MIN_EVALUATION_DAYS:
                ev -= 1
                p += 1
                continue
            break

        if ed >= ev:
            if ev > MIN_EVALUATION_DAYS and p > ev:
                ev -= 1
                ed += 1
                continue
            if p > MIN_PROPOSAL_DAYS and p > ev:
                p -= 1
                ed += 1
                continue
            break

        break

    return p, ed, ev


def calculate_phase_deadlines(start_datetime, total_days):
    """
    総期限日数から3つの期限を計算する。

    方針（total_days >= MIN_TOTAL_DAYS のとき）:
    - 提案:編集:評価の基準比率を **4:2:3** とし（4:2:4 の体感に近いが評価を提案より短く）、
      Hamilton（最大剰余法）で整数化したあと、**提案 > 評価 > 編集** と各最低日数を満たすよう調整する。
    - 編集期間は共創（コメント・返信・編集）のため、1日固定にはしない。

    最低: 提案3日、編集1日、評価2日。total_days は MIN_TOTAL_DAYS 以上 MAX_TOTAL_DAYS 以下。

    Args:
        start_datetime: 開始日時
        total_days: 総日数（カレンダー日ベースでビュー側と揃えた整数）

    Returns:
        tuple: (proposal_deadline, edit_deadline, evaluation_deadline)

    Raises:
        ValueError: total_days が範囲外の場合
    """
    if total_days < MIN_TOTAL_DAYS:
        raise ValueError(
            f"期限まで最低{MIN_TOTAL_DAYS}日必要です"
            f"（提案{MIN_PROPOSAL_DAYS}日、編集{MIN_EDIT_DAYS}日、評価{MIN_EVALUATION_DAYS}日）"
        )
    if total_days > MAX_TOTAL_DAYS:
        raise ValueError(
            f"課題の総日数は最大{MAX_TOTAL_DAYS}日までです（提案・編集・評価の合計）。"
        )

    proposal_days, edit_days, evaluation_days = _allocate_phase_days_ratio(total_days)

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