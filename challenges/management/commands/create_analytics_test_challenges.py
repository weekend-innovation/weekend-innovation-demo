"""
独創性・支持率・影響度の検証用テストデータ作成コマンド

3つの課題（各30件の解決案、合計90件）を contributor_1 で作成。
全フェーズ完了（結果画面表示可能）の状態にし、proposer_1 は3課題全てに提案。
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

CHALLENGES = [
    {
        "title": "【検証用】持続可能な都市交通の実現に向けた解決策",
        "description": "自動車依存の削減、公共交通の拡充、マイクロモビリティの活用など、持続可能な都市交通を実現するための具体的な解決策を募集します。",
    },
    {
        "title": "【検証用】高齢化社会における地域コミュニティの維持・活性化",
        "description": "少子高齢化が進む中、地域のつながりを維持し、孤立を防ぐための取り組みやサービスアイデアを募集します。",
    },
    {
        "title": "【検証用】若年層のキャリア形成を支援する仕組み",
        "description": "学校と社会の接続、職業教育の充実、メンタリング制度など、若者のキャリア形成を支援する新しい仕組みを募集します。",
    },
]

# 30件分の解決案テンプレート（結論・推論の組み合わせで多様性を確保）
PROPOSAL_TEMPLATES = [
    ("ライドシェアと公共交通の統合アプリ", "既存の交通手段をシームレスに連携し、ルート最適化で利便性と環境負荷低減を両立する。"),
    ("ゾーン30の拡大と歩行者優先区域の設定", "車の速度制限と歩行者の安全確保により、地域の住みやすさを向上させる。"),
    ("コミュニティバスのオンデマンド運行", "需要に応じた柔軟なルートで、過疎地域の移動手段を確保する。"),
    ("シェアサイクルのステーション拡充", "駅周辺から生活圏までカバーし、ラストワンマイルの課題を解決する。"),
    ("高齢者向け送迎サービスのボランティア連携", "地域住民が主体的に関わる仕組みで、持続可能なサポートを実現する。"),
    ("見守りカフェのネットワーク化", "公民館や商店と連携し、気軽に参加できる居場所を増やす。"),
    ("世代間交流イベントの定期開催", "若者と高齢者が互いに学び合う場を設け、社会的孤立を防ぐ。"),
    ("地域包括支援センターの機能強化", "相談窓口のワンストップ化と、民間との連携を進める。"),
    ("インターンシップの必修化と単位認定", "実務経験を教育に組み込み、キャリアの早期形成を支援する。"),
    ("メンター制度のマッチングプラットフォーム", "業界経験者と若者をつなぎ、具体的なキャリア相談を可能にする。"),
    ("職業体験プログラムの拡充", "中学校・高校段階から多様な職種に触れ、将来の選択肢を広げる。"),
    ("キャリアコンサルティングの公的支援", "無料または低価格で専門家のアドバイスを受けられるようにする。"),
    ("サテライトオフィスの郊外展開", "通勤負担を軽減し、地域雇用を創出する。"),
    ("電動キックボードのシェアリング", "短距離移動の新選択肢として、環境負荷の低い手段を提供する。"),
    ("買い物弱者支援のデリバリー連携", "スーパーと自治体が連携し、食品アクセスを確保する。"),
    ("地域SNSによる情報共有", "高齢者でも使いやすいツールで、地域の情報交換を促進する。"),
    ("企業説明会のオンライン化", "地方在住の学生も大企業の情報にアクセスできるようにする。"),
    ("副業・兼業の認知拡大", "多様なキャリアパスを社会規範として受け入れる。"),
    ("技能実習制度の見直し", "外国人材の定着と地域貢献を両立する新たな枠組みを検討する。"),
    ("EV充電インフラの整備", "電動化の普及に必要な充電スポットを戦略的に配置する。"),
    ("フリースクールへの公的支援", "多様な学びの場を選択肢として認め、支援する。"),
    ("起業家教育の必修化", "学校段階からアントレプレナーシップを育成する。"),
    ("リカレント教育の補助金拡充", "社会人の学び直しを経済的に支援する。"),
    ("テレワーク推奨日の設定", "企業が一斉に在宅勤務を行うことで、通勤混雑を緩和する。"),
    ("地域密着型コワーキングスペース", "在宅勤務者の isolation を防ぎ、地域交流を生む。"),
    ("子ども食堂のネットワーク拡大", "食を通じた居場所づくりと、生活支援を組み合わせる。"),
    ("学び直しの税制優遇", "自己投資を促す仕組みで、キャリア転換を後押しする。"),
    ("マッチングアプリによる婚活支援", "地域の出会いの場をオンラインとオフラインで補完する。"),
    ("ジョブシャドウイングの普及", "短時間の職業観察を通じて、仕事の実態を理解する。"),
    ("ポートフォリオ評価の導入", "学歴以外の能力を示す手段として、採用に活用する。"),
]


class Command(BaseCommand):
    help = "独創性・支持率・影響度検証用に3課題×30解決案のテストデータを作成"

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

        # 課題 closed 時の自動分析シグナルを一時無効化（本コマンドで分析を実行するため）
        post_save.disconnect(analytics_signals.auto_analyze_on_challenge_close, sender=Challenge)

        # 既存の【検証用】課題を削除（二重表示を防ぐ）
        existing = Challenge.objects.filter(
            contributor=contributor,
            title__startswith="【検証用】",
        )
        deleted_count = existing.count()
        existing.delete()
        if deleted_count > 0:
            self.stdout.write(
                self.style.WARNING(f"既存の【検証用】課題 {deleted_count} 件を削除しました。")
            )

        now = timezone.now()
        # 全フェーズが終了するように、開始を30日前に設定
        start = now - timedelta(days=30)
        total_days = 7
        deadline = start + timedelta(days=total_days)
        deadline = deadline.replace(hour=23, minute=59, second=59, microsecond=999999)
        proposal_deadline, edit_deadline, evaluation_deadline = calculate_phase_deadlines(start, total_days)

        reward_amount = Decimal(str(calculate_reward_amount(required_count)))
        adoption_reward = Decimal("500000")

        with transaction.atomic():
            created_challenges = []
            for i, ch_data in enumerate(CHALLENGES):
                challenge = Challenge.objects.create(
                    title=ch_data["title"],
                    description=ch_data["description"],
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
                # 影響度のホットネス計算用に、課題開始日を過去に設定
                Challenge.objects.filter(pk=challenge.pk).update(created_at=start)
                challenge.refresh_from_db()

                # 選出（proposer_1 含む50人）
                selection = SelectionService.create_selection(challenge, required_count=required_count)
                selection.selected_users.set(eligible[:required_count])
                selection.selected_count = len(eligible[:required_count])
                selection.status = "completed"
                selection.completed_at = now
                selection.save()
                SelectionService._assign_anonymous_names(challenge, eligible[:required_count])

                # 30件の解決案（proposer_1 は必ず1件目）
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

                # 解決案の created_at を period 内に分散（ホットネス検証用）
                mid = start + (edit_deadline - start) / 2
                for idx, p in enumerate(proposals):
                    # 一部は後半に偏らせる（インデックスで制御）
                    if idx % 5 == 0:  # 6件目、11件目... は後半に集中
                        base = mid
                    else:
                        base = start + timedelta(hours=idx * 2)
                    if base > edit_deadline:
                        base = edit_deadline - timedelta(hours=1)
                    Proposal.objects.filter(pk=p.pk).update(created_at=base)

                # 評価・コメント用に proposals を再取得（created_at 反映）
                proposals = list(Proposal.objects.filter(challenge=challenge).order_by("id"))

                # 各提案者について、他者の解決案を評価
                for evaluator in proposers_for_proposals:
                    evaluated = 0
                    for prop in proposals:
                        if prop.proposer_id == evaluator.id:
                            continue
                        # 独創性: proposal インデックスに応じて score を変える (0,1,2)
                        score_var = (prop.id + evaluator.id) % 3  # 0,1,2
                        score = score_var
                        # 支持率: insight_score 1-5 を変える
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
                        evaluated += 1

                    UserEvaluationCompletion.objects.update_or_create(
                        challenge=challenge,
                        user=evaluator,
                        defaults={
                            "has_completed_all_evaluations": True,
                            "completed_at": now,
                        },
                    )

                # コメント（影響度検証用）: 件数・ユニーク・後半集中をばらつかせる
                commenters_pool = [u for u in proposers_for_proposals if u.id != proposer_1.id][:20]
                comment_time_map = {}  # (proposal_id, k) -> datetime
                for idx, prop in enumerate(proposals):
                    n_comments = (idx % 6) + 2  # 2〜7件
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

                # 参考編集（支持率検証用）: 一部の提案に追加
                for idx in [3, 8, 15]:
                    if idx < len(proposals):
                        prop = proposals[idx]
                        comments = list(ProposalComment.objects.filter(proposal=prop, is_deleted=False)[:2])
                        for comm in comments:
                            ProposalEditReference.objects.get_or_create(
                                proposal=prop,
                                comment=comm,
                            )

                created_challenges.append(challenge)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"課題 {challenge.id} 作成: {challenge.title} ({len(proposals)}件の解決案)"
                    )
                )

            # 分析実行
            if not options.get("skip_analysis"):
                for ch in created_challenges:
                    try:
                        analyzer = ChallengeAnalyzer(ch.id)
                        analyzer.analyze_challenge()
                        self.stdout.write(self.style.SUCCESS(f"分析完了: 課題 {ch.id}"))
                    except Exception as e:
                        self.stderr.write(self.style.ERROR(f"分析エラー 課題 {ch.id}: {e}"))

        # シグナルを再度有効化
        post_save.connect(analytics_signals.auto_analyze_on_challenge_close, sender=Challenge)

        self.stdout.write(
            self.style.SUCCESS(
                f"完了: 3課題作成。課題ID: {[c.id for c in created_challenges]}。"
                "proposer_1 でログインし、各課題の結果画面を確認してください。"
            )
        )
