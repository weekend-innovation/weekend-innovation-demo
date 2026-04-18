"""
散布図の散らばり確認用の課題データ作成

contributor_1 による50人選出。40件の解決案（1件はproposer_1）。
全フェーズ完了。解決案は多様なテーマで構成し、TF-IDFクラスタリングで散らばるようにする。
※散布図のモデルは変更せず、課題・解決案の内容のみ調整。
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

CHALLENGE_TITLE = "地域・社会の多様な課題解決アイデアの募集"
CHALLENGE_DESCRIPTION = (
    "持続可能な未来のための多様な視点を募集します。"
    "技術、環境、教育、医療、交通、文化など、あらゆる分野からの解決案を歓迎します。"
)

# 40件分。テーマごとに異なる語彙を使用し、TF-IDFで散らばるようにする
PROPOSAL_TEMPLATES = [
    # 技術・AI
    ("人工知能の教育活用", "プログラミング教育とAI教材で次世代人材を育成する。"),
    ("量子コンピュータの実用化", "暗号解析や創薬など新たなアプリケーションを開拓する。"),
    ("ブロックチェーンの透明性", "選挙や契約の改ざん防止に分散型台帳を活用する。"),
    # 環境・気候
    ("森林再生と二酸化炭素吸収", "大規模植林でカーボンオフセットを実現する。"),
    ("海洋プラスチックの回収技術", "海中ロボットでマイクロプラスチックを除去する。"),
    ("地熱発電の普及促進", "火山国日本の地熱資源を再生可能エネルギーに活用する。"),
    # 教育・人材
    ("職業訓練校の拡充", "リスキリング施設を全国に展開し転職支援を強化する。"),
    ("留学生の就職支援", "日本語教育と企業マッチングで海外人材の定着を図る。"),
    ("義務教育のプログラミング強化", "小学校から論理的思考とコーディングを学ばせる。"),
    # 医療・健康
    ("遠隔診療の恒久化", "オンライン診療を通常診療として定着させる。"),
    ("認知症予防の栄養指導", "食生活改善で認知機能の維持を支援する。"),
    ("精神科医の偏在解消", "テレメンタルで地方のメンタルケアを充実させる。"),
    # 農業・食料
    ("スマート農業の導入", "ドローンとセンサーで効率的な農作業を実現する。"),
    ("食品ロスの削減", "フードバンクと賞味期限延長で廃棄を減らす。"),
    ("有機栽培の補助金拡充", "化学肥料を使わない農業を支援する。"),
    # 交通・物流
    ("鉄道の無人運転化", "ATOと監視システムで人手不足に対応する。"),
    ("電動キックボードの規制整備", "市街地のラストワンマイルを電動化する。"),
    ("貨物鉄道の復権", "トラックから鉄道へのモーダルシフトを促進する。"),
    # 都市・まちづくり
    ("コンパクトシティの推進", "徒歩圏に生活機能を集約し郊外の空洞化を防ぐ。"),
    ("空き家の有効活用", "リノベーションでシェアハウスや拠点として再生する。"),
    ("歩行者専用ゾーンの拡大", "中心市街地を歩行者天国化し賑わいを創出する。"),
    # 文化・芸術
    ("伝統工芸のデジタルアーカイブ", "3Dスキャンで技を記録し次世代に継承する。"),
    ("公立図書館の充実", "貸出冊数の上限撤廃と電子書籍の導入を進める。"),
    ("屋外音楽フェスの支援", "地域の観光と若者文化を両立させる。"),
    # スポーツ
    ("オリンピック施設の民間委譲", "大会後に跡地をスポーツクラブなどに転用する。"),
    ("障がい者スポーツの普及", "パラリンピック種目を学校体育に取り入れる。"),
    ("eスポーツの教育導入", "ゲームを教材にチームワークと戦略思考を育む。"),
    # 福祉・介護
    ("介護ロボットの導入補助", "移乗や見守りを自動化し負担を軽減する。"),
    ("障害者雇用の法定率引き上げ", "民間2.3%から3%へ段階的に引き上げる。"),
    ("ひとり親世帯の住宅支援", "公営住宅の優先入居と家賃補助を拡充する。"),
    # 観光・地域
    ("観光公害の規制", "民泊の届出制と入域規制で住民生活を守る。"),
    ("農泊の推進", "農家民宿で田舎体験と所得向上を両立させる。"),
    ("歴史街道の整備", "古道を歩けるルートとして観光資源化する。"),
    # その他多様
    ("移住支援金の拡充", "地方へのUターン・Iターンを金銭で後押しする。"),
    ("週休3日制の実験", "企業単位で試行し生産性とQOLを検証する。"),
    ("ベーシックインカムの検証", "限定地域でモデル実験を実施する。"),
    ("防災訓練のデジタル化", "VRで津波や地震の避難体験をシミュレーションする。"),
    ("地域通貨の実験", "商店街で利用できるポイントで地元経済を回す。"),
    ("宇宙産業の育成", "衛星データを農業や漁業の効率化に活用する。"),
    ("河川の自然再生", "護岸を撤去し湿地を復元して生物多様性を取り戻す。"),
]


class Command(BaseCommand):
    help = "散布図散らばり確認用の課題（50人選出、40解決案・多様テーマ）を作成"

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
                f"http://localhost:3000/challenges/{challenge.id} で散布図を確認してください。"
            )
        )
