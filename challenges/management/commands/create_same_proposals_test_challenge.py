"""
テスト用：全く同じ内容の解決案30件の課題を作成

散布図や「最も～な解決案」のプレーンな状態を確認するため。
評価・コメントは不要。
"""
from datetime import timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from django.db.models.signals import post_save

from challenges.models import Challenge, calculate_phase_deadlines
from challenges.views import calculate_reward_amount
from selections.services import SelectionService
from selections.models import ChallengeUserAnonymousName
from proposals.models import Proposal
from challenge_analytics import signals as analytics_signals
from challenge_analytics.services import ChallengeAnalyzer

User = get_user_model()

# 全30件で同じ内容
SAME_CONCLUSION = "テスト用の結論です。全ての解決案が同一内容で、クラスタリングや分析結果のプレーンな状態を確認します。"
SAME_REASONING = "テスト用の推論です。評価やコメントは付与されていません。"


class Command(BaseCommand):
    help = "テスト用：同じ内容の解決案30件の課題を作成（評価・コメントなし）"

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-analysis",
            action="store_true",
            help="分析実行をスキップする",
        )

    def handle(self, *args, **options):
        try:
            contributor = User.objects.get(username="contributor_1", user_type="contributor")
        except User.DoesNotExist:
            self.stderr.write(self.style.ERROR("contributor_1 が見つかりません。"))
            return

        required_count = 30
        eligible = SelectionService.get_eligible_users(Challenge(contributor=contributor))
        if len(eligible) < required_count:
            self.stderr.write(
                self.style.ERROR(
                    f"提案者が{len(eligible)}人しかいません。30人以上の proposer が必要です。"
                )
            )
            return

        post_save.disconnect(analytics_signals.auto_analyze_on_challenge_close, sender=Challenge)

        # 既存の「テスト（2026/2/17）」課題を削除
        existing = Challenge.objects.filter(
            contributor=contributor,
            title="テスト（2026/2/17）",
        )
        deleted_count = existing.count()
        existing.delete()
        if deleted_count > 0:
            self.stdout.write(self.style.WARNING(f"Deleted {deleted_count} existing test challenge(s)."))

        now = timezone.now()
        start = now - timedelta(days=30)
        total_days = 7
        deadline = start + timedelta(days=total_days)
        deadline = deadline.replace(hour=23, minute=59, second=59, microsecond=999999)
        proposal_deadline, edit_deadline, evaluation_deadline = calculate_phase_deadlines(
            start, total_days
        )

        reward_amount = Decimal(str(calculate_reward_amount(required_count)))
        adoption_reward = Decimal("500000")

        with transaction.atomic():
            challenge = Challenge.objects.create(
                title="テスト（2026/2/17）",
                description="散布図・最も～な解決案のプレーンな状態を確認するためのテスト課題です。全ての解決案は同一内容です。",
                contributor=contributor,
                reward_amount=reward_amount,
                adoption_reward=adoption_reward,
                required_participants=required_count,
                deadline=deadline,
                proposal_deadline=proposal_deadline,
                edit_deadline=edit_deadline,
                evaluation_deadline=evaluation_deadline,
                status="closed",
            )
            Challenge.objects.filter(pk=challenge.pk).update(created_at=start)
            challenge.refresh_from_db()

            selection = SelectionService.create_selection(challenge, required_count=required_count)
            selected_users = eligible[:required_count]
            selection.selected_users.set(selected_users)
            selection.selected_count = len(selected_users)
            selection.status = "completed"
            selection.completed_at = now
            selection.save()
            SelectionService._assign_anonymous_names(challenge, selected_users)

            for proposer in selected_users:
                try:
                    cuan = ChallengeUserAnonymousName.objects.get(challenge=challenge, user=proposer)
                    anon = cuan.anonymous_name
                except ChallengeUserAnonymousName.DoesNotExist:
                    anon = None
                Proposal.objects.create(
                    challenge=challenge,
                    proposer=proposer,
                    conclusion=SAME_CONCLUSION,
                    reasoning=SAME_REASONING,
                    anonymous_name=anon,
                    is_anonymous=True,
                    status="submitted",
                )

        post_save.connect(analytics_signals.auto_analyze_on_challenge_close, sender=Challenge)

        if not options.get("skip_analysis"):
            try:
                analyzer = ChallengeAnalyzer(challenge.id)
                analyzer.analyze_challenge()
                self.stdout.write(self.style.SUCCESS(f"Analysis done: Challenge ID {challenge.id}"))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"分析エラー: {e}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Done: Challenge 'Test (2026/2/17)' created (ID: {challenge.id}). "
                f"30 identical proposals. Login as contributor_1 to view scatter plot and analysis."
            )
        )
