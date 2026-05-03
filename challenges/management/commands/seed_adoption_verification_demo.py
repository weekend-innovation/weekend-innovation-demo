"""
採用・結果画面の確認用デモデータを投入する。

- 投稿者: weekend-innovation-3（--contributor-username で変更可）
- 既存の提案者プールからランダムに30名を選出（--count、--seed）
- 解決案30件 + 全員が他者の解決案を評価済み（UserEvaluationCompletion 反映）
- 各期限を過去にし、課題 status=closed（採用確定前の「期限切れ」状態）

削除用: purge_adoption_verification_demo（タイトル接頭辞 DEMO_TITLE_PREFIX と一致する課題のみ）。
DEMO_TITLE_PREFIX は purge コマンドと同期すること。

安全メモ: 本番で試す場合は 2026-05-03 23:59 (Asia/Tokyo) までに
`purge_adoption_verification_demo` または `--if-after-deadline` を推奨。
"""

from __future__ import annotations

import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models.signals import post_save
from django.utils import timezone

from challenges.models import Challenge, calculate_phase_deadlines
from challenges.views import calculate_reward_amount
from challenge_analytics import signals as analytics_signals
from challenge_analytics.services import ChallengeAnalyzer
from proposals.models import Proposal, ProposalEvaluation
from selections.models import ChallengeUserAnonymousName, UserEvaluationCompletion
from selections.services import SelectionService

User = get_user_model()

# purge_adoption_verification_demo.py と同じ値に保つこと
DEMO_TITLE_PREFIX = "【デモ採用確認・5/3削除予定】"

CHALLENGE_TITLE = f"{DEMO_TITLE_PREFIX} 地域産業とデジタル活用の両立モデル検討"

CHALLENGE_DESCRIPTION = (
    "地方の伝統産業や中小企業が、人手不足や市場縮小に直面する中で、デジタル技術や新たな連携モデルにより"
    "持続的に価値を生み続ける施策を検討するデモ課題です。\n\n"
    "※確認用データです。不要になったら管理コマンド purge_adoption_verification_demo で削除してください。"
    "2026年5月3日 23:59 (JST) までの運用を想定。"
)

TOTAL_DAYS = 7

PROPOSAL_TEMPLATES: list[tuple[str, str]] = [
    (
        "地域工芸とECを組み合わせた受注生産モデル",
        "職人の手元在庫負荷を抑えつつ、受注情報をクラウド化し最短納期を提示できる仕組みを提案する。",
    ),
    (
        "小規模事業者向け共通バックオフィス支援プラットフォーム",
        "人事・請求・在庫のミニ機能を共用化し固定費を下げつつ運用品質を揃える。",
    ),
    (
        "高齤化地域向けオンラップと電話オペレーションのハイブリッド窓口",
        "オンライン完結だけでなく電話での伴走により利用者離脱を防ぐ。",
    ),
    (
        "観光地混雑の平準化としての時間帯予約連携サービス",
        "既存インフラに手を添え過剰開発を避けつつ旅行者行動データを活用する。",
    ),
    (
        "産学官連携の短期PoC支援パッケージ",
        "8週間で仮説検証→採否判断まで持っていく標準スキームと契約ひな型。",
    ),
    (
        "再エネ立地とデータセンター排熱の地域熱利用",
        "排熱を地域熱供給と農業ハウス暖房に転用するシナジー設計を示す。",
    ),
    (
        "農産物ブランド共有マーケの共同保有スキーム",
        "複数産地でロゴやストーリーを共通化し広告費の分散投下を実現する。",
    ),
    (
        "災害時に中小物流事業者を束ねる広域協定モデル",
        "平常時研修と非常時のみ発動される指揮系統テンプレを用意する。",
    ),
    (
        "工場写真・熟練動画を学習補助に使う技能伝承OSS",
        "現場許諾プロセスまで含んだオープンデザインを明示する。",
    ),
    (
        "公的助成×民間開発のゲート型マッチング",
        "助成付与条件を段階化し失敗コストを下げる入札前審査を入れる。",
    ),
    (
        "脱炭素建材の共同調達と性能保証の束ね買い",
        "性能保証をまとめて契約し中小建設会社の採用障壁を下げる。",
    ),
    (
        "地方銀行APIと地域ポイントの相互送金実験",
        "相互送金で街外貨幣流出を抑えつつ利用データを自治体に還元する。",
    ),
    (
        "シェア工房と職人マッチングの保険付き契約",
        "事故責任を明確化し工房の空き時間を安全に流通させる。",
    ),
    (
        "漁獲予測と魚価安定の共同購買バイヤー制度",
        "卸と消費地小売が共同で予測情報を買い上げるインセンティブ設計。",
    ),
    (
        "空き家バンクとリノベ施工者の信頼スコア連携",
        "施工品質をスコア化し投資家・移住者の意思決定コストを下げる。",
    ),
    (
        "学校給食地産地消のロット追跡ブロックチェーン軽量版",
        "重厚な台帳ではなく配送単位のハッシュ連鎖で最小コストを狙う。",
    ),
    (
        "医療×介護のタスク共有チケット制",
        "境界領域の依頼をチケット化し滞留可視化でケア連続性を上げる。",
    ),
    (
        "地域FMとポッドキャストの広告在庫統合",
        "中小スポンサーがまとめてリーチを買える簡易DSPを提示する。",
    ),
    (
        "河川管理と市民通報の写真位置情報連携",
        "通報の位置精度を上げる軽量アプリと自治体ワークフロー整備。",
    ),
    (
        "観光バス動的ルーティングによる渋滞分散",
        "事前予約データでルートを日次最適化し観光客体験を守る。",
    ),
    (
        "中小メーカーの海外展示会共同出展パッケージ",
        "ブース・通訳・物流を束ね単価を下げる年次スキーム。",
    ),
    (
        "林業残材のチップ化と小規模バイオマス発電の分散接続",
        "送電制約下でも需給調整可能なスモールグリッドを描く。",
    ),
    (
        "商店街空き店舗のショートレット実験制度",
        "高額テナント不要で3か月単位の実験出店を可能にするルール。",
    ),
    (
        "地域観光DXの「翻訳・決済・クーポン」一体SDK",
        "既存観光アプリへ差し込める最小SDKで導入摩擦を下げる。",
    ),
    (
        "漁協と外食チェーンの需要予測共有リーグ",
        "匿名化した販売トレンドを共有し廃棄と品切れを同時に減らす。",
    ),
    (
        "高スキル人材の週末リモート派遣と地域税還元",
        "都市部人材の余剰時間を地方に流し還元金を地域基金に入れる。",
    ),
    (
        "文化財修繕のクラウドファンディング返礼品標準化",
        "返礼品設計の事務コストを下げ修繕案件の立ち上げを早める。",
    ),
    (
        "地方空港とドローン物流ハブの段階接続プラン",
        "規制段階に合わせたロードマップで投資家説明を容易にする。",
    ),
    (
        "中小企業のサイバー保険と診断バンドル販売",
        "診断→改善→保険のワンストップで採用率を上げる。",
    ),
    (
        "地域スポーツクラブの施設共有カレンダー標準",
        "二重予約と空き資産浪費を同時に減らす相互運用フォーマット。",
    ),
    (
        "漁港スマート灯台と小型気象センサの共同設置",
        "漁業安全と観光安全の双方にデータを再利用する。",
    ),
]


class Command(BaseCommand):
    help = "weekend-innovation-3 向け・採用確認用の期限切れ課題（30名・評価済み）を作成"

    def add_arguments(self, parser):
        parser.add_argument(
            "--contributor-username",
            default="weekend-innovation-3",
            help="課題を所有する投稿者のユーザー名",
        )
        parser.add_argument(
            "--count",
            type=int,
            default=30,
            help="選出・解決案の人数（既定30）",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=None,
            help="乱数シード（再現用）",
        )
        parser.add_argument(
            "--replace",
            action="store_true",
            help="同一接頭辞の既存課題をこの投稿者から削除してから作成",
        )
        parser.add_argument(
            "--skip-analysis",
            action="store_true",
            help="期限切れ課題のクラスタリング/分析生成をスキップ",
        )

    def handle(self, *args, **options):
        username = options["contributor_username"]
        count: int = options["count"]
        seed = options["seed"]

        try:
            contributor = User.objects.get(username=username, user_type="contributor")
        except User.DoesNotExist:
            db_cfg = settings.DATABASES.get("default", {})
            engine = db_cfg.get("ENGINE", "?")
            name = db_cfg.get("NAME", "?")
            self.stderr.write(
                self.style.ERROR(
                    f"投稿者ユーザー「{username}」(user_type=contributor) が見つかりません。\n\n"
                    f"よくある原因: 管理画面では Render 本番ユーザーを見ているのに、"
                    f"このコマンドは別のデータベース（例: ローカル SQLite）につながっている。\n"
                    f"現在の接続: ENGINE={engine} NAME={name}\n\n"
                    "本番に課題を作りたい場合は、DATABASE_URL が本番 Postgres を指す環境で実行するか、"
                    "GitHub Actions 等から同じ設定で実行してください。"
                    "ローカルの db.sqlite3 だけでは本番ユーザーは存在しません。"
                )
            )
            return

        temp = Challenge(contributor=contributor)
        eligible = list(SelectionService.get_eligible_users(temp))
        if len(eligible) < count:
            self.stderr.write(
                self.style.ERROR(
                    f"選出可能な提案者が {len(eligible)} 人しかいません（要 {count} 人）。"
                    "先に提案者アカウントを用意してください。"
                )
            )
            return

        if seed is not None:
            random.seed(seed)
        selected_users = random.sample(eligible, count)

        if options["replace"]:
            deleted, _ = Challenge.objects.filter(
                contributor=contributor,
                title__startswith=DEMO_TITLE_PREFIX,
            ).delete()
            if deleted:
                self.stdout.write(self.style.WARNING(f"既存デモ課題を削除しました（関連 {deleted} 件）。"))

        post_save.disconnect(analytics_signals.auto_analyze_on_challenge_close, sender=Challenge)
        try:
            self._create_challenge(
                contributor=contributor,
                selected_users=selected_users,
                count=count,
                skip_analysis=options["skip_analysis"],
            )
        finally:
            post_save.connect(analytics_signals.auto_analyze_on_challenge_close, sender=Challenge)

    def _create_challenge(
        self,
        *,
        contributor: User,
        selected_users: list,
        count: int,
        skip_analysis: bool,
    ) -> None:
        now = timezone.now()
        start = now - timedelta(days=30)
        proposal_deadline, edit_deadline, evaluation_deadline = calculate_phase_deadlines(start, TOTAL_DAYS)
        deadline = evaluation_deadline

        reward_amount = Decimal(str(calculate_reward_amount(count)))
        adoption_reward = Decimal("500000")

        self.stdout.write(
            "課題・選出・解決案・評価を作成しています（リモート DB ではしばらく無音になります）…"
        )

        with transaction.atomic():
            challenge = Challenge.objects.create(
                title=CHALLENGE_TITLE,
                description=CHALLENGE_DESCRIPTION,
                contributor=contributor,
                reward_amount=reward_amount,
                adoption_reward=adoption_reward,
                required_participants=count,
                deadline=deadline,
                proposal_deadline=proposal_deadline,
                edit_deadline=edit_deadline,
                evaluation_deadline=evaluation_deadline,
                status="closed",
            )
            Challenge.objects.filter(pk=challenge.pk).update(created_at=start)
            challenge.refresh_from_db()

            selection = SelectionService.create_selection(challenge, required_count=count)
            selection.selected_users.set(selected_users)
            selection.selected_count = count
            selection.status = "completed"
            selection.completed_at = now
            selection.save()
            SelectionService._assign_anonymous_names(challenge, selected_users)

            proposals: list[Proposal] = []
            for i, proposer in enumerate(selected_users):
                conclusion, reasoning = PROPOSAL_TEMPLATES[i % len(PROPOSAL_TEMPLATES)]
                cuan = ChallengeUserAnonymousName.objects.filter(
                    challenge=challenge, user=proposer
                ).first()
                anon = cuan.anonymous_name if cuan else None
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
                base = mid if idx % 5 == 0 else start + timedelta(hours=idx * 2)
                if base > edit_deadline:
                    base = edit_deadline - timedelta(hours=1)
                Proposal.objects.filter(pk=p.pk).update(created_at=base)

            proposals = list(Proposal.objects.filter(challenge=challenge).order_by("id"))

            for evaluator in selected_users:
                for prop in proposals:
                    if prop.proposer_id == evaluator.id:
                        continue
                    score_var = (prop.id + evaluator.id) % 3
                    insight_var = (prop.id * 7 + evaluator.id) % 5 + 1
                    ProposalEvaluation.objects.get_or_create(
                        proposal=prop,
                        evaluator=evaluator,
                        defaults={
                            "evaluation": ["yes", "maybe", "no"][score_var],
                            "insight_level": str(insight_var),
                        },
                    )
                UserEvaluationCompletion.objects.update_or_create(
                    challenge=challenge,
                    user=evaluator,
                    defaults={"has_completed_all_evaluations": True, "completed_at": now},
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"作成完了: 課題 ID={challenge.id} / 選出+解決案={count}名 / status={challenge.status} / "
                f"phase={challenge.get_current_phase()}"
            )
        )

        if not skip_analysis:
            self.stdout.write(
                "クラスタリング／分析を実行しています（外部 API により数分〜かかることがあります）。"
                "画面だけ先に確認する場合は次回から --skip-analysis を付けてください。"
            )
            try:
                ChallengeAnalyzer(challenge.id).analyze_challenge()
                self.stdout.write(self.style.SUCCESS(f"分析ジョブ完了: 課題 {challenge.id}"))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"分析エラー（手動で再実行可）: {e}"))
