"""
来年の世界経済と日本経済の課題データ作成

contributor_1 による50人選出の課題を作成。
「来年の世界の経済状況とそれに対する日本経済の動向」
40件の解決案（1件はproposer_1）。全フェーズ完了（結果画面表示可能）の状態にする。
"""
import random
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
from selections.models import ChallengeUserAnonymousName, UserEvaluationCompletion
from proposals.models import (
    Proposal, ProposalComment, ProposalEvaluation,
    ProposalEditReference
)
from challenge_analytics import signals as analytics_signals
from challenge_analytics.services import ChallengeAnalyzer

User = get_user_model()

CHALLENGE_TITLE = "来年の世界の経済状況とそれに対する日本経済の動向"
CHALLENGE_DESCRIPTION = (
    "2026年の世界経済の見通しと、それに応じた日本経済の動きについて、"
    "具体的な視点や対策を募集します。米中関係、金利動向、為替、エネルギー、"
    "地政学リスク、デジタル経済など、多様な観点からの解決案を歓迎します。"
)

# 40件分の解決案テンプレート（結論・理由。世界経済と日本経済について多様な視点）
PROPOSAL_TEMPLATES = [
    ("米中関係の安定化が鍵", "米中経済対話の進展と、日本が両国とのバランスを保つ外交・経済政策が重要。"),
    ("金利正常化への段階的対応", "欧米の金利動向を注視し、日本は財政健全化と民間投資の両立を図る。"),
    ("円安・円高リスクのヘッジ", "為替変動に強い輸出・輸入のバランスと、内需主導の経済構造への転換。"),
    ("エネルギー安全保障の強化", "再生可能エネルギーと原発再稼働のバランスで、供給安定性を確保する。"),
    ("半導体・先端技術の国内投資", "サプライチェーンのリスク分散と、国内製造拠点の強化を進める。"),
    ("労働力不足への対応", "移民政策の見直しと、AI・自動化による生産性向上を組み合わせる。"),
    ("財政再建と成長の両立", "歳出削減と成長分野への投資を同時に進め、持続可能な財政を目指す。"),
    ("インフレ期待の適正化", "日銀の金融政策と、賃金上昇と物価の好循環を実現する政策設計。"),
    ("デジタル経済の推進", "DX投資と、中小企業のデジタル化支援で国際競争力を高める。"),
    ("アジア地域との連携強化", "東南アジア・インドとの経済連携を深め、サプライチェーンの多様化を図る。"),
    ("気候変動と経済政策の統合", "脱炭素投資を成長の原動力とし、グリーンボンド等で資金を調達する。"),
    ("不動産市場の健全化", "金利上昇を見据えた住宅ローン規制と、過剰債務の早期是正。"),
    ("スタートアップ・イノベーション支援", "ベンチャー投資と、大企業とのオープンイノベーションを促進する。"),
    ("所得格差の是正", "賃金底上げと、教育・再就職支援で中間層の底上げを図る。"),
    ("観光・サービス輸出の拡大", "インバウンド回復と、高付加価値サービスの海外展開を加速する。"),
    ("農業・食料安全保障", "国内生産の強化と、輸入先の多元化で食料供給の安定を確保する。"),
    ("金融機関の健全性維持", "金利変動リスク管理と、デジタル金融への対応を強化する。"),
    ("製造業の強靭化", "国内回帰と、自動車・部品産業のEV・EV化への対応を急ぐ。"),
    ("地方経済の活性化", "デジタル移住と、地方創生への投資で地域経済を再生する。"),
    ("社会保障制度の持続可能性", "年金・医療・介護の改革と、負担と給付のバランスを再設計する。"),
    ("地政学リスクへの備え", "台湾有事等を想定し、経済・エネルギー・物流のBCPを整備する。"),
    ("中央銀行デジタル通貨の検討", "決済インフラの強化と、国際協調を見据えたCBDCの研究を進める。"),
    ("貿易ルールの活用", "CPTPP・RCEPを軸に、ルールベースの貿易秩序を維持・強化する。"),
    ("人的資本への投資", "リスキリングと、高等教育・職業訓練の充実で人材を育成する。"),
    ("企業ガバナンスの強化", "ESG経営と、株主・ステークホルダーとの対話を促進する。"),
    ("規制改革の推進", "成長分野での規制緩和と、消費者保護のバランスを取る。"),
    ("財政政策の効率化", "無駄削減と、効果の高い公共投資にリソースを集中させる。"),
    ("中小企業の支援強化", "資金繰り支援と、サプライチェーン再編への移行支援を行う。"),
    ("大学・研究開発への投資", "基礎研究と産学連携を強化し、イノベーションの土台を固める。"),
    ("女性・高齢者の労働参加", "働き方改革と、保育・介護インフラの整備を進める。"),
    ("海外直接投資の呼び込み", "法人税優遇と、規制の透明性向上で日本への投資を促進する。"),
    ("物流・インフラの効率化", "港湾・空港の強化と、国内物流のデジタル化を推進する。"),
    ("医療・ヘルスケア産業の育成", "予防医療と、医療データ活用で新産業を創出する。"),
    ("金融リテラシーの向上", "家計の資産形成と、リスク管理能力の向上を支援する。"),
    ("国際協調のリーダーシップ", "G7等で日本の立場を発信し、国際経済秩序の再構築に貢献する。"),
    ("災害・危機対応力の強化", "大規模災害に備えた経済システムの冗長性と復旧力を持つ。"),
    ("労働生産性の向上", "業務プロセスの見直しと、テレワーク・柔軟働き方の定着を図る。"),
    ("カーボンニュートラルへの移行", "2050年目標に向け、産業構造の転換を計画的に進める。"),
    ("テクノロジー人材の確保", "海外人材の受け入れと、国内でのIT教育の強化を両立させる。"),
    ("経済統計・政策評価の高度化", "リアルタイムデータと、エビデンスに基づく政策立案を推進する。"),
]


class Command(BaseCommand):
    help = "来年の世界経済・日本経済の課題（50人選出、40解決案）を作成"

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

        try:
            proposer_1 = User.objects.get(username="proposer_1", user_type="proposer")
        except User.DoesNotExist:
            self.stderr.write(self.style.ERROR("proposer_1 が見つかりません。"))
            return

        required_count = 50
        eligible = SelectionService.get_eligible_users(Challenge(contributor=contributor))
        if len(eligible) < required_count:
            self.stderr.write(
                self.style.WARNING(
                    f"提案者が{len(eligible)}人しかいません。選出人数を{len(eligible)}に調整します。"
                )
            )
            required_count = len(eligible)

        if proposer_1 not in eligible:
            eligible = [proposer_1] + [u for u in eligible if u.id != proposer_1.id][: required_count - 1]
        else:
            eligible = [proposer_1] + [u for u in eligible if u.id != proposer_1.id][: required_count - 1]

        if len(eligible) < 40:
            self.stderr.write(
                self.style.ERROR(
                    f"提案者が40人未満です（{len(eligible)}人）。40人以上のproposerが必要です。"
                )
            )
            return

        post_save.disconnect(analytics_signals.auto_analyze_on_challenge_close, sender=Challenge)

        now = timezone.now()
        start = now - timedelta(days=30)
        total_days = 7
        deadline = start + timedelta(days=total_days)
        deadline = deadline.replace(hour=23, minute=59, second=59, microsecond=999999)
        proposal_deadline, edit_deadline, evaluation_deadline = calculate_phase_deadlines(start, total_days)

        reward_amount = Decimal(str(calculate_reward_amount(required_count)))
        adoption_reward = Decimal("500000")

        with transaction.atomic():
            challenge = Challenge.objects.create(
                title=CHALLENGE_TITLE,
                description=CHALLENGE_DESCRIPTION,
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
            selection.selected_users.set(eligible[:required_count])
            selection.selected_count = len(eligible[:required_count])
            selection.status = "completed"
            selection.completed_at = now
            selection.save()
            SelectionService._assign_anonymous_names(challenge, eligible[:required_count])

            proposers_for_proposals = [proposer_1] + [
                u for u in eligible[:required_count] if u.id != proposer_1.id
            ][:39]

            proposals = []
            for j, proposer in enumerate(proposers_for_proposals):
                conclusion, reasoning = PROPOSAL_TEMPLATES[j % len(PROPOSAL_TEMPLATES)]
                try:
                    cuan = ChallengeUserAnonymousName.objects.get(challenge=challenge, user=proposer)
                    anon = cuan.anonymous_name
                except ChallengeUserAnonymousName.DoesNotExist:
                    anon = None
                p = Proposal.objects.create(
                    challenge=challenge,
                    proposer=proposer,
                    conclusion=conclusion,
                    reasoning=reasoning,
                    anonymous_name=anon,
                    is_anonymous=True,
                    status="submitted",
                )
                proposals.append(p)

            mid = start + (edit_deadline - start) / 2
            for idx, p in enumerate(proposals):
                if idx % 5 == 0:
                    base = mid
                else:
                    base = start + timedelta(hours=idx * 2)
                if base > edit_deadline:
                    base = edit_deadline - timedelta(hours=1)
                Proposal.objects.filter(pk=p.pk).update(created_at=base)

            proposals = list(Proposal.objects.filter(challenge=challenge).order_by("id"))

            for evaluator in proposers_for_proposals:
                for prop in proposals:
                    if prop.proposer_id == evaluator.id:
                        continue
                    score_var = (prop.id + evaluator.id) % 3
                    score = score_var
                    insight_var = (prop.id * 7 + evaluator.id) % 5 + 1
                    ProposalEvaluation.objects.get_or_create(
                        proposal=prop,
                        evaluator=evaluator,
                        defaults={
                            "evaluation": ["yes", "maybe", "no"][score],
                            "score": score,
                            "insight_level": str(insight_var),
                            "insight_score": insight_var,
                        },
                    )

                UserEvaluationCompletion.objects.update_or_create(
                    challenge=challenge,
                    user=evaluator,
                    defaults={
                        "has_completed_all_evaluations": True,
                        "completed_at": now,
                    },
                )

            commenters_pool = [u for u in proposers_for_proposals if u.id != proposer_1.id][:20]
            comment_time_map = {}
            for idx, prop in enumerate(proposals):
                n_comments = (idx % 6) + 2
                for k in range(n_comments):
                    if idx % 3 == 0 and k >= n_comments // 2:
                        comment_time = mid + timedelta(hours=k)
                    else:
                        comment_time = start + timedelta(hours=idx * 3 + k)
                    if comment_time > edit_deadline:
                        comment_time = edit_deadline - timedelta(minutes=1)
                    comment_time_map[(prop.id, k)] = comment_time

            for idx, prop in enumerate(proposals):
                n_comments = (idx % 6) + 2
                for k in range(n_comments):
                    c = random.choice(commenters_pool)
                    comm = ProposalComment.objects.create(
                        proposal=prop,
                        commenter=c,
                        target_section="reasoning",
                        conclusion="参考になりました",
                        reasoning=f"提案{idx+1}へのコメント{k+1}です。",
                        is_deleted=False,
                    )
                    ct = comment_time_map.get((prop.id, k), start + timedelta(hours=idx))
                    ProposalComment.objects.filter(pk=comm.pk).update(created_at=ct)

            for idx in [3, 8, 15, 22]:
                if idx < len(proposals):
                    prop = proposals[idx]
                    comments = list(ProposalComment.objects.filter(proposal=prop, is_deleted=False)[:2])
                    for comm in comments:
                        ProposalEditReference.objects.get_or_create(
                            proposal=prop,
                            comment=comm,
                        )

            self.stdout.write(
                self.style.SUCCESS(
                    f"課題 {challenge.id} 作成: {challenge.title} ({len(proposals)}件の解決案)"
                )
            )

            if not options.get("skip_analysis"):
                try:
                    analyzer = ChallengeAnalyzer(challenge.id)
                    analysis = analyzer.analyze_challenge()
                    src = getattr(analysis, "recommendations_source", "") if analysis else ""
                    if src == "llm":
                        self.stdout.write(self.style.SUCCESS(f"分析完了: 課題 {challenge.id}（Gemini総括生成済み）"))
                    else:
                        self.stdout.write(self.style.WARNING(f"分析完了: 課題 {challenge.id}（総括はテンプレート。LLM未使用: {src or '不明'}）"))
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"分析エラー 課題 {challenge.id}: {e}"))

        post_save.connect(analytics_signals.auto_analyze_on_challenge_close, sender=Challenge)

        self.stdout.write(
            self.style.SUCCESS(
                f"完了: 課題ID {challenge.id}。"
                f"http://localhost:3000/challenges/{challenge.id} で結果画面を確認してください。"
            )
        )
