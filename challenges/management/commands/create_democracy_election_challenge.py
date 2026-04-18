"""
クラスタリング検証用テストデータ作成コマンド

contributor_1 による50人選出の課題を作成。
「世界での民主主義を踏まえて、日本での2月の衆院選をどのような視点で考えるのがベストか」
30件の解決案。全フェーズ完了（結果画面表示可能）の状態にする。
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

CHALLENGE_TITLE = "世界での民主主義を踏まえて、日本での2月の衆院選をどのような視点で考えるのがベストか"
CHALLENGE_DESCRIPTION = (
    "世界各国の民主主義の現状を踏まえ、日本における衆議院議員選挙（2月実施想定）を"
    "どのような視点で捉え、評価すべきかについての解決案を募集します。"
)

# 30件分の解決案テンプレート（結論・推論の組み合わせ。クラスタリングで多様なグループができるよう、視点を分散）
PROPOSAL_TEMPLATES = [
    ("有権者の投票率向上施策", "若年層や無党派層の政治参加を促すため、オンライン投票や期日前投票の拡充を進める。"),
    ("メディアの公平性と報道の自由", "多様な意見が届くよう、公共放送と民間メディアの役割分担を明確にし、事実に基づく報道を担保する。"),
    ("デジタルデモクラシーの活用", "SNSやデジタルプラットフォームを活用した有権者との双方向コミュニケーションを推進する。"),
    ("少子高齢化と世代間格差の視点", "社会保障や財政を世代間でどう負担するか、選挙を通じて有権者が選択できる仕組みを議論する。"),
    ("外交・安全保障政策の争点化", "国際情勢を踏まえ、日米同盟や地域安全保障について明確な選択肢を提示する。"),
    ("経済政策の是非を問う", "インフレ対策、雇用、成長戦略について、各党の違いをわかりやすく比較する。"),
    ("教育と人材育成の国家戦略", "教育無償化やリカレント教育など、人材投資の観点から政策を評価する。"),
    ("地方分権と地域主権の深化", "一極集中の是正と地方の自律性を高める観点で、選挙の争点を設定する。"),
    ("憲法改正の是非を争点に", "改憲の是非を正面から問い、国民的議論を深める機会として選挙を位置づける。"),
    ("環境・気候変動政策の比較", "脱炭素やエネルギー政策について、各党のビジョンを比較し有権者が選択できるようにする。"),
    ("所得格差と再分配の視点", "税制や社会保障の再分配機能を問い直し、格差是正の観点で政策を比較する。"),
    ("移民・外国人政策の議論", "労働力不足と多文化共生のバランスをどう取るか、国際比較の視点で議論する。"),
    ("政治資金と政治倫理の透明化", "政治献金や政党助成金の透明性を高め、政治への信頼を回復する。"),
    ("国会改革と立法プロセスの見直し", "与野党の対話や審議の質を高めるため、国会運営の改革を争点にする。"),
    ("司法と三権分立の役割", "司法の独立性と民主的コントロールのバランスを、選挙を通じて議論する。"),
    ("女性の政治参画の促進", "クオータ制や候補者選定の透明化など、女性の政治参加を促す施策を評価する。"),
    ("若者の政治教育の強化", "主権者教育や模擬選挙など、若年層の政治リテラシーを高める取り組みを支援する。"),
    ("インターネット選挙運動の拡充", "ネットを活用した政策発信と有権者との接点を拡大し、情報格差を縮小する。"),
    ("ポピュリズムへの対応", "感情的アピールと政策論争のバランスをどう取るか、民主主義の質を問う。"),
    ("国際比較の視点での評価", "欧米やアジアの選挙制度と比較し、日本の選挙の特徴と課題を明らかにする。"),
    ("政党政治の再編と二大政党制", "政党の役割と政権交代の可能性について、有権者が選択できる争点を設定する。"),
    ("危機管理とリーダーシップ", "災害やパンデミックを踏まえ、指導者の資質を選挙でどう問うか議論する。"),
    ("社会保障の持続可能性", "年金・医療・介護の財源と給付のバランスを、選挙の主要な争点として提示する。"),
    ("イノベーションと産業政策", "研究開発投資や規制改革など、成長産業の育成を政策比較の観点に含める。"),
    ("農林水産業と食料安全保障", "一次産業の支援と食料自給率を、選挙の争点として位置づける。"),
    ("都市と農村の格差是正", "地域間格差の解消を、選挙を通じて問う視点を導入する。"),
    ("原発とエネルギー政策", "原発依存度と再エネへの転換を、有権者が選択できる争点として明確にする。"),
    ("労働政策と働き方改革", "非正規と正規の格差是正やワークライフバランスを、選挙の争点に含める。"),
    ("金融政策と財政規律", "金融緩和と財政再建のバランスを、政策論争の中心に据える。"),
    ("多様性と包摂の社会づくり", "LGBTQや障害者など、多様な人々が参加できる社会を選挙の視点に含める。"),
]


class Command(BaseCommand):
    help = "クラスタリング検証用：民主主義・衆院選の課題（50人選出、30解決案）を作成"

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

        if len(eligible) < 30:
            self.stderr.write(
                self.style.ERROR(
                    f"提案者が30人未満です（{len(eligible)}人）。30人以上のproposerが必要です。"
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
            ][:29]

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

            for idx in [3, 8, 15]:
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
                    analyzer.analyze_challenge()
                    self.stdout.write(self.style.SUCCESS(f"分析完了: 課題 {challenge.id}"))
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"分析エラー 課題 {challenge.id}: {e}"))

        post_save.connect(analytics_signals.auto_analyze_on_challenge_close, sender=Challenge)

        self.stdout.write(
            self.style.SUCCESS(
                f"完了: 課題ID {challenge.id}。"
                f"http://localhost:3000/challenges/{challenge.id} で結果画面を確認してください。"
            )
        )
