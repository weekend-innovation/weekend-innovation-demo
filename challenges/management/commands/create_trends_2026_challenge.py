"""
結果画面の様々なケース確認用テストデータ作成コマンド

contributor_1 による50人選出の課題を作成。
「2026年流行を生み出すためには、どのような要件が必要だと考えられますか」
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

CHALLENGE_TITLE = "2026年流行を生み出すためには、どのような要件が必要だと考えられますか"
CHALLENGE_DESCRIPTION = (
    "2026年に新たな流行を生み出すために、どのような要件・条件・仕組みが必要だと考えられるか、"
    "具体的な解決案を募集します。テクノロジー、文化、サステナビリティ、健康など、多様な視点を歓迎します。"
)

# 40件分の解決案テンプレート（結論・推論。2026年流行の要件について多様な視点）
PROPOSAL_TEMPLATES = [
    ("Z世代・α世代のニーズを起点に設計する", "デジタルネイティブ層の価値観や消費行動を深く理解し、その共感を得られる体験を先行して作る。"),
    ("サステナビリティとトレンドの統合", "環境負荷の低い素材・プロセスを前提にしつつ、デザイン性と経済性を両立させる。"),
    ("AIによるパーソナライズ体験の進化", "生成AIやレコメンド技術で、個人に最適化された体験を低コストで提供できる仕組みを整える。"),
    ("ローカル×グローバルのハイブリッド", "地域の文化や資源を活かしつつ、デジタルで世界中に届ける双方向の仕組みを構築する。"),
    ("感情・体験経済へのシフト", "モノの所有より、その瞬間の体験や感情の共有に価値を置くサービス設計を行う。"),
    ("メタバース・XRの実用化", "仮想空間と現実の接点を増やし、新しい社交・体験の場を日常に組み込む。"),
    ("マイクロインフルエンサーの活用", "大規模ではなく、信頼性の高い小規模インフルエンサーとの継続的な協働を設計する。"),
    ("サブスクリプション型の定着", "単発購入ではなく、継続的な関係性とアップデートを前提としたビジネスモデルを構築する。"),
    ("オープンイノベーションの加速", "自社だけでなく、スタートアップや異業種との共創により、スピードと多様性を確保する。"),
    ("データドリブンな意思決定", "リアルタイムの市場データやSNS分析を活用し、迅速に仮説検証と軌道修正を行う。"),
    ("デジタルファーストの体験設計", "オンラインを軸にしつつ、オフラインは補完として位置づけ、一貫した体験を提供する。"),
    ("コミュニティ主導の価値創造", "ユーザーが参加・貢献できる仕組みを作り、ファンコミュニティが流行を牽引する構造にする。"),
    ("健康・ウェルビーイングへの統合", "流行を単なる消費ではなく、心身の健康やQOL向上と結びつけた価値提案を行う。"),
    ("短期と長期のバランス", "瞬発力のあるトレンド対応と、中長期で育てるブランド価値の両立を計画的に設計する。"),
    ("クリエイター経済の活用", "個人クリエイターが主役となる経済圏と連携し、彼らの発信力を流行の起点にする。"),
    ("テクノロジーの民主化", "高度な技術やツールを、専門家以外も扱える形で提供し、多様な主体が創造に参加できるようにする。"),
    ("リアルとデジタルの境界の曖昧化", "ARやIoTで現実空間に情報を重ね、新しい体験の層を日常に追加していく。"),
    ("ストーリーテリングの強化", "商品・サービスを単体ではなく、物語や世界観と一体で伝えるコンテンツ戦略を構築する。"),
    ("インクルーシブデザインの採用", "多様なユーザー層を前提に設計し、誰もが参加・享受できる流行を目指す。"),
    ("ガバナンスと信頼の確保", "流行に伴う社会的影響を考慮し、倫理面や法規制を先行して整理する。"),
    ("リアルタイムフィードバックの仕組み", "ユーザーの反応を即時取得し、改善や拡張に反映するループを回す。"),
    ("ライフスタイル提案型のアプローチ", "単品ではなく、生活シーン全体を提案する形で流行を形成する。"),
    ("ノスタルジーと新規性の融合", "懐かしさを喚起する要素と新しい体験を組み合わせ、共感と驚きを両立させる。"),
    ("シェアリング・リユースの拡大", "所有より共有・再利用を前提としたモノ・サービスの設計を行う。"),
    ("ゲーミフィケーションの活用", "遊びや競争の要素を組み込み、参加意欲と継続性を高める。"),
    ("プライバシーとパーソナライズの両立", "個人情報を適切に保護しつつ、価値ある体験を提供する技術と制度を整える。"),
    ("オムニチャネル体験の最適化", "EC、実店舗、SNSなど複数チャネルで一貫した体験を提供し、シームレスに接点を増やす。"),
    ("社会課題との接続", "流行を社会的意義と結びつけ、共感と実効性を高める。"),
    ("フェムテック・ヘルステックの普及", "従来の市場に届いていなかった層に向けた技術とサービスを拡大する。"),
    ("教育・リテラシー向上の投資", "新しい流行を受け入れる土壌を作るため、ユーザーの理解やスキル向上を支援する。"),
    ("トレンド予測と先行投資", "将来のトレンドを予測し、市場が拡大する前にリソースを投下する。"),
    ("フレキシブルな供給体制", "需要の変動に柔軟に対応できるサプライチェーンと生産体制を構築する。"),
    ("ブランディングとストーリーの一貫性", "流行の移ろいの中でも、中核となる価値や世界観を貫く。"),
    ("ユーザー生成コンテンツの促進", "ユーザーが参加・発信しやすくし、UGCが流行の拡散を担う仕組みを作る。"),
    ("インフラの整備と規制緩和", "新しいサービスや体験が普及するための法制度・インフラを整備する。"),
    ("多世代・多文化のクロスオーバー", "年齢や文化の境界を越えた共創・交流が生まれる場や仕組みを設計する。"),
    ("リアル体験の価値向上", "デジタル化が進む中で、実体験の希少性と価値を高めるイベントや空間を提供する。"),
    ("エコシステムの構築", "単体ではなく、周辺サービスやパートナーと連携したエコシステムで価値を最大化する。"),
    ("失敗を許容する実験文化", "小さく試し、早く学ぶ文化を組織に根付かせ、革新的な流行の芽を育てる。"),
    ("透明性とオープンな情報発信", "開発プロセスや背景を公開し、ユーザーの信頼と参加意欲を高める。"),
]


class Command(BaseCommand):
    help = "結果画面確認用：2026年流行の課題（50人選出、40解決案）を作成"

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
