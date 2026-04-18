"""
自治体向け：空き家問題の課題・解決案データ作成

課題：「空き家問題をどのように解決するべきか」
30件の多様な解決案。contributor_1が課題投稿者。前提は以前の課題・解決案と同様。
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

CHALLENGE_TITLE = "【テスト】空き家問題をどのように解決するべきか"
CHALLENGE_DESCRIPTION = (
    "全国で増加する空き家は、防災・防犯・景観の観点から地域課題となっています。"
    "本課題では、自治体や地域コミュニティが取りうる具体的な解決策について、"
    "多様な視点からの解決案を募集します。"
)

PROPOSAL_TEMPLATES = [
    (
        "空き家バンクの整備とマッチング支援：所有者と移住希望者を結ぶプラットフォーム構築",
        "自治体が空き家の登録・情報一元管理を行う空き家バンクを運営し、移住相談窓口と連携する。"
        "補助金の申請窓口も一本化し、空き家の利活用を希望する人々の負担を軽減する。",
    ),
    (
        "空き家改修補助金の拡充とリノベーション工事の費用負担軽減",
        "耐震改修や断熱改修に対する補助率を引き上げ、老朽化した空き家の再生コストを下げる。"
        "リノベーション補助とあわせ、若い世代の取得意欲を高める。",
    ),
    (
        "空き家を地域の交流拠点に：サロン・シェアオフィス・子育てスペースへの転用",
        "所有者から一時的に借り受け、地域住民が集まるサロンや在宅ワーク用のシェアオフィスに活用する。"
        "子育て世帯向けの一時預かりスペースとしても有効で、過疎地域の交流促進につながる。",
    ),
    (
        "空き家の除却費用補助と危険箇所の早期解消",
        "倒壊の恐れがある空き家について、除却費用の一部を自治体が負担する制度を拡大する。"
        "所有者の経済的負担を軽減し、危険空き家の早期解消を促す。",
    ),
    (
        "空き家データベースの整備と GIS による可視化",
        "空き家の位置・状態・所有者意向を一元的に管理し、地図上で可視化する。"
        "政策立案や民間事業者との連携に活用し、効率的な空き家対策を推進する。",
    ),
    (
        "空き家税制の見直し：固定資産税の特例措置と適正管理のインセンティブ設計",
        "空き家を放置する場合の税負担を適正化しつつ、利活用や除却に踏み切った所有者には軽減措置を講じる。"
        "経済的インセンティブにより、所有者の行動変容を促す。",
    ),
    (
        "学生・若者向けシェアハウスへの転換：大学や企業との連携",
        "大学周辺や都市部の空き家を、学生や若手社会人向けのシェアハウスに改修する。"
        "家賃補助や入居者マッチングを自治体が支援し、人口減少地域への若者の定着を図る。",
    ),
    (
        "空き家を災害時仮設住宅の代替拠点として事前登録",
        "大規模災害時に空き家を一時的に被災者に提供する制度を構築する。"
        "事前登録により迅速な供給が可能となり、仮設住宅不足を補完する。",
    ),
    (
        "空き家の相続相談窓口の設置と遺言・任意後見の促進",
        "相続が原因で空き家化する事例が多いため、相続前の相談窓口を設け、遺言や任意後見の利用を促す。"
        "円滑な相続により、空き家の適切な処分・利活用につなげる。",
    ),
    (
        "地域住民による見回り・草刈りボランティアと地域ポイント制度",
        "近隣住民が空き家周辺の見回りや草刈りを行い、地域通貨やポイントで報酬を受け取る仕組みを導入する。"
        "地域のつながりを強化しつつ、空き家の治安・景観を維持する。",
    ),
    (
        "移住定住促進と空き家活用の一体的な支援",
        "移住希望者向けの住宅紹介、就業支援、子育て支援をパッケージで提供する。"
        "空き家を入口に据え、地域全体の人口定着施策と連動させる。",
    ),
    (
        "空き家を福祉施設や介護拠点として活用",
        "高齢化が進む地域では、空き家を小規模多機能型居宅介護やデイサービスの拠点に転用する。"
        "高齢者が住み慣れた地域で暮らせるよう支援し、施設不足を解消する。",
    ),
    (
        "観光拠点・ゲストハウスへの転換と地域ブランディング",
        "観光地や歴史的地区の空き家を、宿泊施設やギャラリーに改修する。"
        "地域の魅力発信と雇用創出を両立し、空き家を地域資源として再位置づける。",
    ),
    (
        "空き家の買取・賃貸仲介を自治体が仲介する公的ファンド",
        "民間の賃貸・売却ニーズと空き家所有者をマッチングし、自治体が信頼性を担保する。"
        "必要な改修費用を自治体が一時立て替え、売却・賃貸成立後に回収する。",
    ),
    (
        "空き家の太陽光発電設置支援とエネルギー地域循環",
        "空き家の屋根に太陽光パネルを設置し、地域の再生可能エネルギー供給拠点とする。"
        "収益の一部を所有者に還元し、空き家の維持管理コストを賄う。",
    ),
    (
        "空き家オーナー向けの無料相談会と利活用セミナー",
        "所有者が空き家の活用方法を知らないケースが多いため、専門家による無料相談会を定期開催する。"
        "賃貸・売却・除却など選択肢を説明し、適切な判断を支援する。",
    ),
    (
        "空き家を農産物の直売所・加工拠点に活用",
        "農業地域の空き家を、直売所や農産物加工の拠点として再生する。"
        "6次産業化と雇用創出により、地域経済の活性化につなげる。",
    ),
    (
        "空き家の適正管理を義務づける条例の強化と罰則の明確化",
        "放置空き家に対する立入調査や是正命令の手続きを明確化し、従わない場合の罰則を強化する。"
        "法的権限を背景に、所有者への働きかけを強める。",
    ),
    (
        "空き家の建築基準法適合証明と耐震診断の補助拡大",
        "古い空き家の耐震診断と改修費用を補助し、建築基準法適合証明を取得しやすくする。"
        "取得済み空き家は融資や入居者の選択肢が広がり、流通を促進する。",
    ),
    (
        "空き家を若い世代の起業・創作活動の拠点に",
        "アーティストや職人、起業家向けに、低家賃で空き家を貸し出す制度を設ける。"
        "地域に新しい人の流れを生み、空き家をクリエイティブな活動の場に転換する。",
    ),
    (
        "空き家の一括管理を民間に委託するモデル事業",
        "自治体が民間の管理会社と契約し、一定数の空き家を一括で管理・維持する。"
        "所有者負担を軽減しつつ、適正管理と利活用の両立を図る。",
    ),
    (
        "空き家を保育・学童施設のサテライトとして活用",
        "待機児童が存在する地域で、空き家を小規模保育や学童保育のサテライト拠点とする。"
        "大規模施設建設よりも迅速に供給でき、地域の子育て支援を強化する。",
    ),
    (
        "自治体による空き家の一時取得とリースバック",
        "所有者から一定期間空き家を借り受け、自治体が改修・管理して第三者に貸し出す。"
        "所有者は収益を得つつ手離さず、自治体は空き家対策を推進できる。",
    ),
    (
        "空き家問題の啓発キャンペーンと所有者への丁寧な説明",
        "空き家を放置することが地域に与える影響を、パンフレットや説明会で丁寧に伝える。"
        "義務感ではなく理解に基づいた行動変容を促す。",
    ),
    (
        "空き家を地域防災の備蓄倉庫や避難所の補完拠点に",
        "災害時の物資備蓄や一時避難所として、空き家を事前登録しておく。"
        "平常時は地域の倉庫としても活用し、防災力を高める。",
    ),
    (
        "空き家の簡易宿所許可取得支援と民泊規制対応",
        "民泊需要がある地域では、空き家の簡易宿所許可取得を自治体が支援する。"
        "適正な届出・許可の下で運営され、無許可民泊の歯止めにもなる。",
    ),
    (
        "空き家オーナーと自治体・NPOの三者協定",
        "所有者・自治体・NPOが協定を結び、空き家の活用方法と管理責任を明確化する。"
        "NPOが運営の中心となり、地域の課題解決と雇用創出を両立する。",
    ),
    (
        "空き家の修繕費用を低利融資で支援する制度",
        "修繕やリフォームに必要な資金を、自治体のファンドや金融機関と連携して低利で貸し付ける。"
        "初期投資のハードルを下げ、空き家の再生を促進する。",
    ),
    (
        "空き家を高齢者の終の棲家として活用する終身賃貸モデル",
        "高齢者が余生を過ごすための終身賃貸契約を、空き家オーナーと結ぶ仕組みを自治体が仲介する。"
        "高齢者の住まい確保と、空き家の安定した利活用を両立する。",
    ),
    (
        "空き家の緑化・庭園活用で景観向上と地域交流",
        "空き家の庭を地域の緑化プロジェクトの対象とし、住民参加で維持管理する。"
        "景観の改善と地域のつながり強化、防犯効果を期待できる。",
    ),
]

class Command(BaseCommand):
    help = "空き家問題の課題（30解決案・自治体向け）を作成"

    def add_arguments(self, parser):
        parser.add_argument("--skip-analysis", action="store_true", help="分析実行をスキップする")

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
            required_count = len(eligible)
        if proposer_1 not in eligible:
            eligible = [proposer_1] + [u for u in eligible if u.id != proposer_1.id][: required_count - 1]
        else:
            eligible = [proposer_1] + [u for u in eligible if u.id != proposer_1.id][: required_count - 1]

        if len(eligible) < 30:
            self.stderr.write(self.style.ERROR(f"提案者が30人未満です（{len(eligible)}人）。"))
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
                base = mid if idx % 5 == 0 else start + timedelta(hours=idx * 2)
                if base > edit_deadline:
                    base = edit_deadline - timedelta(hours=1)
                Proposal.objects.filter(pk=p.pk).update(created_at=base)

            proposals = list(Proposal.objects.filter(challenge=challenge).order_by("id"))

            for evaluator in proposers_for_proposals:
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
                            "score": score_var,
                            "insight_level": str(insight_var),
                            "insight_score": insight_var,
                        },
                    )
                UserEvaluationCompletion.objects.update_or_create(
                    challenge=challenge,
                    user=evaluator,
                    defaults={"has_completed_all_evaluations": True, "completed_at": now},
                )

            commenters_pool = [u for u in proposers_for_proposals if u.id != proposer_1.id][:20]
            for idx, prop in enumerate(proposals):
                n_comments = (idx % 6) + 2
                for k in range(n_comments):
                    c = random.choice(commenters_pool)
                    comm = ProposalComment.objects.create(
                        proposal=prop,
                        commenter=c,
                        target_section="reasoning",
                        conclusion="参考になりました",
                        reasoning=f"空き家問題について、貴重な視点だと思います。地域の実情に合った提案ですね。",
                        is_deleted=False,
                    )
                    ct = start + timedelta(hours=idx * 3 + k)
                    if ct > edit_deadline:
                        ct = edit_deadline - timedelta(minutes=1)
                    ProposalComment.objects.filter(pk=comm.pk).update(created_at=ct)

            for idx in [3, 8, 15, 22]:
                if idx < len(proposals):
                    prop = proposals[idx]
                    comments = list(ProposalComment.objects.filter(proposal=prop, is_deleted=False)[:2])
                    for comm in comments:
                        ProposalEditReference.objects.get_or_create(proposal=prop, comment=comm)

            self.stdout.write(
                self.style.SUCCESS(f"課題 {challenge.id} 作成: {challenge.title[:40]}... ({len(proposals)}件)")
            )

            if not options.get("skip_analysis"):
                try:
                    ChallengeAnalyzer(challenge.id).analyze_challenge()
                    self.stdout.write(self.style.SUCCESS(f"分析完了: 課題 {challenge.id}"))
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"分析エラー: {e}"))

        post_save.connect(analytics_signals.auto_analyze_on_challenge_close, sender=Challenge)
        self.stdout.write(self.style.SUCCESS(f"完了: 課題ID {challenge.id}"))
