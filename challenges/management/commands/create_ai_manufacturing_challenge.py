"""
生成AI×製造業の課題・散布図検証用データ作成

課題：「生成AIの影響により製造業はどのように変化するか、そして、その場合、どのような施策が考えられるか」
30件の解決案（文字数多め）。contributor_1、50人選出、全フェーズ完了。
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

CHALLENGE_TITLE = "生成AIの影響により製造業はどのように変化するか、そして、その場合、どのような施策が考えられるか"
CHALLENGE_DESCRIPTION = (
    "Generative AI（生成AI）の台頭により、製造業の設計・生産・品質管理・サプライチェーン管理など"
    "は大きく変貌する可能性があります。本課題では、その変化の方向性と、企業・政府が取りうる具体的な施策について"
    "多様な視点からの解決案を募集します。"
)

# 30件。結論・推論ともに文字数を多めに（以前のテンプレートより長く）
PROPOSAL_TEMPLATES = [
    (
        "設計フェーズへの生成AI導入による開発期間の大幅短縮と、デジタルツインとの連携による試作コスト削減",
        "生成AIは過去の設計データから最適な形状や材質を提案し、人間の設計者と協働することで開発リードタイムを半減できる。"
        "デジタルツインと組み合わせれば、実機試作前にシミュレーションで検証でき、試作回数の削減につながる。",
    ),
    (
        "製造現場の異常検知・予測保全における生成AIの活用と、熟練技能のデジタル継承",
        "センサーデータと生成AIを組み合わせることで、設備の異常を早期に検知し、故障前にメンテナンスを実施できる。"
        "また、熟練者の技能を動画や音声から学習し、若手への教育ツールとして活用することで、人材不足を補完する。",
    ),
    (
        "品質検査の自動化と、生成AIによる欠陥パターン学習に基づく不良品ゼロへの接近",
        "画像認識AIと生成AIにより、従来は人手に頼っていた外観検査を自動化し、ヒューマンエラーを削減する。"
        "過去の不良品データを学習させることで、これまで検出が難しかった微妙な欠陥も検出可能になる。",
    ),
    (
        "サプライチェーンの需要予測精度向上と、生成AIを活用した動的な在庫最適化",
        "販売データや外部要因を入力とし、生成AIで需要を予測することで、過剰在庫と欠品の両方を抑制する。"
        "リアルタイムな需給変動に対応した発注量の動的調整により、サプライチェーン全体の効率を高める。",
    ),
    (
        "カスタマイズ量産の実現：生成AIによるオーダーメイド設計の自動化とモジュール化",
        "顧客の要望を自然言語で入力すると、生成AIが最適な設計案を複数提示する仕組みを構築する。"
        "モジュール化された部品群と組み合わせることで、小ロット多品種生産を従来比で低コストに実現する。",
    ),
    (
        "人とAIの協働工場：生成AIが作業手順をリアルタイムで提案し、作業者を支援する仕組み",
        "カメラと生成AIにより、作業者の動きを解析し、次の最適動作をARディスプレイで表示する。"
        "新人の習熟速度向上と、ベテラン作業者の負荷軽減を両立させ、生産性と品質を同時に高める。",
    ),
    (
        "製造業の脱炭素化：生成AIによるエネルギー使用量の最適化と再エネ導入シミュレーション",
        "設備の稼働データから生成AIが省エネ施策を提案し、工場全体のエネルギー効率を改善する。"
        "太陽光や蓄電池の導入シミュレーションにより、再エネ比率の段階的な引き上げを計画する。",
    ),
    (
        "中小製造業向けの生成AI活用支援：政府主導のプラットフォームと補助金制度の創設",
        "中小企業が単独で生成AIを導入するには資金と人材が不足している。"
        "国が共通プラットフォームを整備し、補助金と技術支援をセットで提供することで、デジタル格差を解消する。",
    ),
    (
        "従業員のリスキリング支援：製造現場からAI活用人材への転換を促す教育プログラム",
        "単純作業がAIに置き換わる中、従業員にはAIの操作・監視・改善提案といった新たな役割が求められる。"
        "企業と教育機関が連携し、実務に直結したカリキュラムで、現場人材のスキル転換を支援する。",
    ),
    (
        "生成AIによる設計知財の保護と、オープンイノベーションとの両立を図る法整備",
        "生成AIが過去の設計データを学習する際、知的財産権の境界が曖昧になる問題がある。"
        "学習データの出所管理とライセンス枠組みを明確にし、企業間の協働と競争を両立させる制度を設計する。",
    ),
    (
        "ロボット制御の生成AI化：自然言語指示による生産ラインの柔軟な再構成",
        "従来はプログラミングが必要だったロボットの動作を、自然言語で指示できるようにする。"
        "多品種少量生産への対応力が高まり、ライン変更のリードタイムを大幅に短縮できる。",
    ),
    (
        "材料開発の加速：生成AIによる新素材の候補探索と、実験計画の最適化",
        "生成AIが既存の材料データベースから新たな組成やプロセスを提案し、実験の試行回数を削減する。"
        "ベイズ最適化と組み合わせることで、少数の実験で所望の性能を持つ材料に到達する。",
    ),
    (
        "グローバルサプライチェーンのリスク管理：生成AIによる地政学リスクの予測と代替調達先の自動提案",
        "地政学的な不安や気象リスクを生成AIが分析し、調達先の分散や代替ルートを事前に提案する。"
        "事業継続計画（BCP）と連携し、サプライチェーンのレジリエンスを強化する。",
    ),
    (
        "製造業DXの段階的推進：まずはデータの見える化から始め、生成AI活用へと発展させるロードマップ",
        "いきなり生成AIを導入するのではなく、センサーデータの収集・可視化を第一段階とし、"
        "蓄積されたデータを活用して徐々にAI機能を拡張する。中小企業でも無理なく進められる。",
    ),
    (
        "地域産業クラスターの再編：生成AIを中核に据えた産学官連携の強化",
        "地域の大学・研究機関・企業が生成AIの共同利用施設を設け、人材交流と技術移転を促進する。"
        "単独では困難な先進技術へのアクセスを、クラスター参加企業に提供する。",
    ),
    (
        "製造プロセスのカーボンフットプリント算出と、生成AIによる削減シナリオの策定支援",
        "製造工程ごとのCO2排出量を可視化し、生成AIが削減効果の高い工程改善案を優先順位付きで提案する。"
        "Scope3を含めた算出方法の標準化と、国際基準との整合を図る。",
    ),
    (
        "生成AIの製造現場での説明可能性：ブラックボックス化を避け、判断根拠を提示する仕組み",
        "AIの推論結果が説明可能であることは、品質管理と安全の観点から重要である。"
        "決定木やルールベースとのハイブリッド設計により、技術者や監督官が理解できる形で出力する。",
    ),
    (
        "遊休設備のシェアリング：生成AIによる需給マッチングとスケジューリングの最適化",
        "稼働率の低い工作機械や検査設備を、他社とシェアするプラットフォームを構築する。"
        "生成AIが需要予測と設備稼働状況から、最適なマッチングとスケジュールを提案する。",
    ),
    (
        "技能継承の危機に対する生成AI活用：熟練者の暗黙知を形式知化し、後継者育成に活用",
        "熟練者の作業を動画・音声で記録し、生成AIが重要なポイントを抽出してマニュアル化する。"
        "VR/ARと組み合わせて、疑似体験型の教育コンテンツとして若手に提供する。",
    ),
    (
        "生成AIの製造業活用における倫理指針と、人間の最終判断責任の明確化",
        "AIが設計や品質判断に関与する場合、どの段階で人間が関与すべきかを明確にする。"
        "業界団体と政府が共同で倫理指針を策定し、説明責任と安全性を担保する。",
    ),
    (
        "循環型製造への転換：生成AIによる素材のトレーサビリティとリサイクルルートの最適化",
        "製品に埋め込んだ識別子とブロックチェーンで素材の履歴を追跡し、"
        "生成AIがリサイクル・リマニュファクチャリングの最適ルートを提案する。",
    ),
    (
        "輸出依存の軽減と国内調達の強化：生成AIによる国産代替材・代替部品の探索支援",
        "海外調達に依存している部材について、国産の代替候補を生成AIがデータベースから探索する。"
        "調達リスクの分散と、国内産業の活性化を両立させる。",
    ),
    (
        "製造業の働き方改革：生成AIによる業務効率化により生まれた余裕を、残業削減に充当",
        "単純な資料作成や報告書の下書きを生成AIに任せることで、技術者の稼働時間を設計・改善活動に集中させる。"
        "過重労働の是正と、付加価値の高い業務へのシフトを実現する。",
    ),
    (
        "小ロット生産の経済性向上：生成AIによる工程計画の最適化と段取り時間の短縮",
        "多品種少量生産では段取り時間がコストに直結する。"
        "生成AIが品目・数量・納期から最適な生産順序と工具配置を提案し、段取り時間を削減する。",
    ),
    (
        "製造業とサービス業の融合：生成AIを介した製品の状態監視と予知型メンテナンスサービス",
        "製造業が自社製品にセンサーとAIを組み込み、顧客の稼働状況をリアルタイムで把握する。"
        "故障前にメンテナンスを提案するサービスモデルへ転換し、収益の安定化を図る。",
    ),
    (
        "生成AIのセキュリティ対策：製造データの漏洩防止と、AIモデルそのものの保護",
        "設計データや生産情報は企業の競争力の源泉である。"
        "生成AIの学習データへのアクセス制御、モデルの不正利用防止など、セキュリティ基準を業界で共有する。",
    ),
    (
        "障害者雇用の拡大：生成AIによる作業支援インターフェースのカスタマイズ",
        "身体的な制約がある方でも製造現場で活躍できるよう、生成AIが個人の能力に合わせて作業手順や"
        "インターフェースをカスタマイズする。多様な人材の活躍の場を広げる。",
    ),
    (
        "地方の製造業集積地の再生：生成AIを活用した産地ブランドの再構築と需要開拓",
        "伝統的な産地の技術と生成AIを組み合わせ、新製品開発やマーケティングを支援する。"
        "海外需要の開拓や、国内での認知向上を、データ駆動で進める。",
    ),
    (
        "生成AI活用における規制の国際調和：海外展開する日本企業が不公平な競争にさらされないよう制度設計",
        "各国で生成AIの規制が進む中、日本企業が海外で事業を行う際の規制コストを最小化する。"
        "国際標準との整合性を重視しつつ、日本企業の技術力を活かせる枠組みを政府が主導する。",
    ),
    (
        "製造業の持続的成長のための人材確保：生成AI活用を魅力的なキャリアとして若者に発信",
        "製造業は単純労働ではなく、AIと協働する高度な仕事であることを教育現場で伝える。"
        "工場見学やインターンシップに生成AIデモを組み込み、次世代人材の興味を引き出す。",
    ),
]


class Command(BaseCommand):
    help = "生成AI×製造業の課題（30解決案・文字数多め）を作成"

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
                conclusion, reasoning = PROPOSAL_TEMPLATES[j]
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
                        reasoning=f"提案{idx+1}へのコメント{k+1}です。生成AIと製造業の関係について、貴重な視点だと思います。",
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
                    f"課題 {challenge.id} 作成: {challenge.title[:40]}... ({len(proposals)}件の解決案)"
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
                f"http://localhost:3000/challenges/{challenge.id} で散布図を確認してください。"
            )
        )
