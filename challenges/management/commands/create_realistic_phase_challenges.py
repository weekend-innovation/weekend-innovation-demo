"""
デプロイ前確認用:
3期間（提案/編集/評価）それぞれに「実務的な課題」を1件ずつ作成し、
各課題に30件の解決案を自動投入する管理コマンド。

要件:
- 期間別に異なるテーマ
- 各課題30件の解決案
- 期限は calculate_phase_deadlines（基準比率 4:2:3、提案＞評価＞編集）で設定
- それぞれ現在時刻で proposal / edit / evaluation フェーズになるよう開始日時を逆算
"""

from datetime import timedelta
from decimal import Decimal
from typing import List, Dict

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from challenges.models import Challenge, calculate_phase_deadlines
from challenges.views import calculate_reward_amount
from proposals.models import Proposal
from selections.models import ChallengeUserAnonymousName
from selections.services import SelectionService

User = get_user_model()


TOTAL_DAYS = 8  # 通常運用に近い日数（提案4日/編集2日/評価2日）
PROPOSALS_PER_CHALLENGE = 30


CHALLENGE_SPECS: List[Dict[str, object]] = [
    {
        "phase": "proposal",
        "title": "【期間検証:提案】中堅製造業における技能継承と生産性向上を両立する施策",
        "description": (
            "熟練社員の退職が進む中、現場ノウハウを継承しつつ、品質と生産性を維持・向上させるための施策を募集します。"
            "設備投資、人材育成、デジタル活用、運用ルールなど、実行可能性の高い提案を求めます。"
        ),
        "stakeholders": "製造現場・品質保証・人事・情報システム部門",
        "goal": "技能継承と生産性の同時改善",
    },
    {
        "phase": "edit",
        "title": "【期間検証:編集】自治体観光地でオーバーツーリズムと住民生活を両立する施策",
        "description": (
            "来訪者の増加で観光収益は伸びる一方、混雑・騒音・交通負荷が住民生活に影響しています。"
            "住民満足と観光価値を両立するため、運用面・制度面・デジタル面を組み合わせた現実的な解決策を募集します。"
        ),
        "stakeholders": "観光課・交通事業者・商店街・地域住民",
        "goal": "観光価値向上と住民負担軽減の両立",
    },
    {
        "phase": "evaluation",
        "title": "【期間検証:評価】自治体における要配慮者の災害時避難支援を高度化する施策",
        "description": (
            "高齢者や障害者、在宅医療利用者など要配慮者の避難支援体制を、平時準備から発災時運用まで一体で見直す課題です。"
            "名簿整備、情報連携、地域協力、訓練設計を含めた実行可能な提案を募集します。"
        ),
        "stakeholders": "危機管理課・福祉部門・医療機関・自治会",
        "goal": "避難支援の実効性向上と初動迅速化",
    },
]


def build_templates(stakeholders: str, goal: str) -> List[Dict[str, str]]:
    actions = [
        "部門横断の推進会議を月次開催し、意思決定を一本化する",
        "現場ヒアリングを定例化し、課題優先順位をデータで決める",
        "試行導入（PoC）を3か月単位で回し、効果検証後に本格展開する",
        "既存業務フローを可視化し、ムダ工程を削減して標準化する",
        "外部パートナー連携を見直し、役割分担とSLAを明確化する",
        "住民・利用者向けの窓口導線を再設計し、問い合わせを減らす",
        "運用ルールを文書化し、担当者交代時の引き継ぎ品質を上げる",
        "KPIダッシュボードを整備し、進捗を週次で共有する",
        "研修計画を職位別に設計し、実務に直結する育成へ切り替える",
        "既存システム連携をAPI化し、二重入力と転記ミスを削減する",
    ]
    methods = [
        "初期費用を抑えるため、既存資産を活用した段階導入を採用する",
        "現場の抵抗を減らすため、評価指標を『負担軽減』中心に設計する",
        "定量指標に加え、利用者満足度の定性評価も併用する",
        "緊急時運用を想定し、平時から訓練とシミュレーションを実施する",
        "担当部門だけでなく、関係者全体で責任分担を定義する",
        "業務停止リスクを避けるため、並行稼働期間を十分に確保する",
        "利用者視点の導線検証を行い、UI/説明文の改善を繰り返す",
        "規程改定と実務運用を同時に進め、制度面の遅れを防ぐ",
        "月次レビューで未達要因を分析し、翌月施策に反映する",
        "費用対効果を可視化し、予算説明責任を果たせる形にする",
    ]
    outcomes = [
        "導入後6か月で処理時間を15%以上短縮できる見込み",
        "属人化を減らし、担当交代時の品質低下リスクを抑制できる",
        "問い合わせ件数の削減と一次解決率向上が期待できる",
        "現場負荷を平準化し、繁忙期でも対応品質を保てる",
        "意思決定の遅延を減らし、施策実行スピードを高められる",
        "関係者連携が円滑になり、重複対応や漏れを防げる",
        "運用コストを抑えながら、住民・顧客体験を改善できる",
        "データに基づく改善サイクルが回り、再現性が高まる",
        "短期成果と中長期の制度定着を両立できる",
        "現実的な予算規模で段階的な成果創出が可能になる",
    ]

    templates: List[Dict[str, str]] = []
    for i in range(PROPOSALS_PER_CHALLENGE):
        action = actions[i % len(actions)]
        method = methods[(i * 3) % len(methods)]
        outcome = outcomes[(i * 5) % len(outcomes)]
        conclusion = f"{action}ことで、{goal}を実現する"
        reasoning = (
            f"対象関係者: {stakeholders}。"
            f"{method}。"
            f"{outcome}。"
            "小規模導入→評価→拡張の順で進めることで、現場負担と失敗リスクを抑えながら定着させる。"
        )
        templates.append({"conclusion": conclusion, "reasoning": reasoning})
    return templates


class Command(BaseCommand):
    help = "Create 3 phase challenges and 30 proposals each"

    def handle(self, *args, **options):
        try:
            contributor = User.objects.get(username="contributor_1", user_type="contributor")
        except User.DoesNotExist:
            self.stderr.write(self.style.ERROR("contributor_1 was not found."))
            return

        eligible = SelectionService.get_eligible_users(Challenge(contributor=contributor))
        if len(eligible) < PROPOSALS_PER_CHALLENGE:
            self.stderr.write(
                self.style.ERROR(
                    f"Not enough proposers (required: {PROPOSALS_PER_CHALLENGE}, current: {len(eligible)}). "
                    "Cannot create 30 proposals per challenge."
                )
            )
            return

        # proposer_1 を優先的に含める（存在すれば先頭へ）
        try:
            proposer_1 = User.objects.get(username="proposer_1", user_type="proposer")
            selected_users = [proposer_1] + [u for u in eligible if u.id != proposer_1.id]
        except User.DoesNotExist:
            selected_users = list(eligible)
        selected_users = selected_users[:max(50, PROPOSALS_PER_CHALLENGE)]

        required_count = min(50, len(selected_users))
        reward_amount = Decimal(str(calculate_reward_amount(required_count)))
        adoption_reward = Decimal("500000")
        now = timezone.now()

        # 重複回避のため旧データを削除（期間検証プレフィックス）
        old_challenges = Challenge.objects.filter(
            contributor=contributor,
            title__startswith="【期間検証:"
        )
        if old_challenges.exists():
            count = old_challenges.count()
            old_challenges.delete()
            self.stdout.write(self.style.WARNING(f"Deleted existing phase test challenges: {count}"))

        phase_start = {
            # now <= proposal_deadline になるよう、開始を1日前
            "proposal": now - timedelta(days=1),
            # proposal_deadline < now <= edit_deadline になるよう、開始を5日前
            "edit": now - timedelta(days=5),
            # edit_deadline < now <= evaluation_deadline になるよう、開始を7日前
            "evaluation": now - timedelta(days=7),
        }

        created = []
        with transaction.atomic():
            for spec in CHALLENGE_SPECS:
                phase = spec["phase"]
                start = phase_start[phase]
                proposal_deadline, edit_deadline, evaluation_deadline = calculate_phase_deadlines(start, TOTAL_DAYS)
                deadline = evaluation_deadline

                challenge = Challenge.objects.create(
                    title=spec["title"],
                    description=spec["description"],
                    contributor=contributor,
                    reward_amount=reward_amount,
                    adoption_reward=adoption_reward,
                    required_participants=required_count,
                    deadline=deadline,
                    proposal_deadline=proposal_deadline,
                    edit_deadline=edit_deadline,
                    evaluation_deadline=evaluation_deadline,
                    status="open",
                )
                # 「通常投稿」に近く見えるよう、作成日時は開始時刻に寄せる
                Challenge.objects.filter(pk=challenge.pk).update(created_at=start)
                challenge.refresh_from_db()

                selection = SelectionService.create_selection(challenge, required_count=required_count)
                selection.selected_users.set(selected_users[:required_count])
                selection.selected_count = required_count
                selection.status = "completed"
                selection.completed_at = now
                selection.save()
                SelectionService._assign_anonymous_names(challenge, selected_users[:required_count])

                templates = build_templates(spec["stakeholders"], spec["goal"])
                proposers_for_proposals = selected_users[:PROPOSALS_PER_CHALLENGE]
                for i, proposer in enumerate(proposers_for_proposals):
                    cuan = ChallengeUserAnonymousName.objects.filter(challenge=challenge, user=proposer).first()
                    anon = cuan.anonymous_name if cuan else None
                    p = Proposal.objects.create(
                        challenge=challenge,
                        proposer=proposer,
                        conclusion=templates[i]["conclusion"],
                        reasoning=templates[i]["reasoning"],
                        anonymous_name=anon,
                        is_anonymous=True,
                        status="submitted",
                    )
                    # 最新寄りに並ぶよう、提案作成時刻を段階的に分散
                    Proposal.objects.filter(pk=p.pk).update(
                        created_at=now - timedelta(hours=(PROPOSALS_PER_CHALLENGE - i))
                    )

                created.append(challenge)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created challenge id={challenge.id} phase={challenge.current_phase}"
                    )
                )

        self.stdout.write(self.style.SUCCESS("Done: created 3 phase challenges and 30 proposals each."))
