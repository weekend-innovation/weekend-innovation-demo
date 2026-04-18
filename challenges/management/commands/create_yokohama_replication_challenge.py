"""
【再現】横浜市製造業×地方創生の課題・解決案（実際の人の評価を再現）

課題：「横浜市に存在する製造業として、地方創生のための新商品又は新サービスを考えてください」
30件の多様な解決案。評価・コメントは実際の人が評価した場合を想定して割り当て。
管理コマンド内にロジックを集約（他課題に影響なし）。
"""


def _get_innovation_eval(innovation_level: int, prop_id: int, evaluator_id: int) -> tuple:
    """独創性評価 (evaluation, score) を返す。No=独創的"""
    x = (prop_id + evaluator_id) % 20
    if innovation_level == 0:
        if x < 15:
            return ("yes", 0)
        return ("maybe", 1) if x < 19 else ("no", 2)
    if innovation_level == 1:
        if x % 4 == 0:
            return ("yes", 0)
        return ("maybe", 1) if x % 4 in (1, 2) else ("no", 2)
    if x == 0:
        return ("yes", 0)
    return ("maybe", 1) if x <= 3 else ("no", 2)


def _get_insight_score(insight_level: int, prop_id: int, evaluator_id: int) -> int:
    """支持率スコア 1-5"""
    offset = (prop_id + evaluator_id) % 3 - 1
    return max(1, min(5, insight_level + offset))


def _get_comment_count(impact_tier: int, prop_id: int) -> int:
    """影響度に応じたコメント数"""
    if impact_tier == 0:
        return 2 + (prop_id % 3)
    if impact_tier == 1:
        return 4 + (prop_id % 3)
    return 6 + (prop_id % 4)


def _get_comment_timing_ratio(impact_tier: int, prop_id: int, k: int, total: int) -> float:
    """コメントの時期（0=前半、1=後半）。影響度高→後半に集中"""
    if impact_tier == 0:
        return 0.2 + 0.3 * (k / max(1, total))
    if impact_tier == 1:
        return 0.3 + 0.4 * (k / max(1, total))
    return 0.5 + 0.5 * (k / max(1, total))


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

CHALLENGE_TITLE = "【再現】横浜市に存在する製造業として、地方創生のための新商品又は新サービスを考えてください"
CHALLENGE_DESCRIPTION = (
    "横浜市には多様な製造業が集積しており、地域の雇用と産業を支えています。"
    "本課題では、横浜の製造業が地方創生に貢献する新商品や新サービスについて、"
    "地域との連携や社会的価値の創出を視野に入れた解決案を募集します。"
)

# (結論, 理由, innovation_level, insight_level, impact_tier)
PROPOSAL_TEMPLATES = [
    ("横浜の地場産材を使った都市型木工製品の開発と直売所との連携",
     "市内の間伐材や再生木材を活用し、都市部で需要のある小物・家具を製造する。"
     "地元の直売所や百貨店と提携し、横浜発のブランドとして販路を開拓する。", 0, 4, 1),
    ("横浜港を活かした輸出向け加工食品の開発と海外展開",
     "横浜の食品製造業が、日本の味を海外向けにアレンジした加工食品を開発する。"
     "横浜港の物流ネットワークを活用し、アジア諸国への輸出を拡大する。", 0, 4, 1),
    ("地元農家と連携した6次産業化プロダクトの共同開発",
     "神奈川県内の農家が育てた野菜や果物を使ったジャム・漬物・ドレッシングを共同開発する。"
     "製造業の加工技術と農家の生産力を結び付け、地域の付加価値を高める。", 0, 4, 1),
    ("横浜開港の歴史を活かした観光土産の企画・製造",
     "開港や港町の歴史をモチーフにした記念品や菓子を開発し、観光客向けに販売する。"
     "ストーリー性のある商品により、横浜の魅力発信と地域経済の活性化を図る。", 0, 4, 0),
    ("廃校・空き施設を活用した地域工房と体験型製造サービス",
     "地方の廃校や空き施設を工房として借り受け、製造体験やワークショップを提供する。"
     "観光と製造を組み合わせ、地域への人の流れと雇用を創出する。", 1, 3, 2),
    ("地元大学との産学連携による新素材・新製品の開発",
     "横浜・神奈川の大学と共同で、地域の特性を活かした新素材や新製品を研究・開発する。"
     "学生のインターンシップ受け入れと合わせ、人材育成にも貢献する。", 1, 4, 1),
    ("障害者就労継続支援との協働：分業による製品製造",
     "地域の就労継続支援A型・B型事業所と協働し、製品の一部工程を委託する。"
     "雇用の場を広げつつ、地域社会との結びつきを強化する。", 1, 4, 2),
    ("地元食材を使った企業・学校給食向け加工品の提供",
     "地域の学校給食や社食向けに、地元農水産物を使った冷凍・加工食品を納入する。"
     "地産地消を推進し、地域の食の安全と農業振興に寄与する。", 0, 4, 1),
    ("地方の伝統工芸とコラボした現代的な生活用品の開発",
     "日本各地の伝統工芸産地と提携し、現代の生活に合うデザインで共同商品を開発する。"
     "横浜から全国の産地へ発信し、地方創生の輪を広げる。", 1, 4, 1),
    ("再生可能エネルギー機器の製造と地域への導入支援",
     "太陽光パネルや蓄電池などの製造と、地域の施設への導入・維持をセットで提供する。"
     "地方の脱炭素化とエネルギーの地産地消を支援する。", 2, 3, 2),
    ("地域の高齢者向け見守り・健康支援製品の開発",
     "センサーやIoTを活用した見守り機器や、高齢者が使いやすい生活用品を開発する。"
     "地域の福祉と連携し、高齢者が住み慣れた場所で安心して暮らせるよう支援する。", 1, 4, 1),
    ("横浜発のサブスクリプション型定期便サービスの立ち上げ",
     "毎月届く地元の特産品や製造品の詰め合わせを、サブスク形式で提供する。"
     "リピート需要を確保しつつ、地域の魅力を継続的に発信する。", 2, 3, 2),
    ("地方の若者向け職業訓練プログラムと製造現場での実習",
     "地域の若者が製造業で働くための研修プログラムを企画し、自社工場で実習の場を提供する。"
     "地方の雇用創出と人材確保の両立を図る。", 0, 4, 1),
    ("地域イベント・祭りとの連携による限定商品の開発",
     "各地の祭りやイベントに合わせた限定商品を開発し、会場や地域の小売店で販売する。"
     "イベントの盛り上げと地域経済の活性化に貢献する。", 0, 3, 1),
    ("リサイクル・アップサイクル素材を使った環境配慮型製品",
     "廃プラスチックや廃木材を原料にした新製品を開発し、サステナブルなブランドを構築する。"
     "環境意識の高い消費者に訴求し、地域の循環型社会づくりに寄与する。", 2, 4, 2),
    ("地方観光ルートとの連携：製造拠点見学ツアーの企画",
     "工場見学や製造体験を組み込んだ観光ツアーを、旅行会社や自治体と共同で企画する。"
     "製造業の魅力を発信し、地域への来訪者を増やす。", 0, 4, 1),
    ("地域の小規模店舗向けノウハウ・機器の提供サービス",
     "地域の個人商店や農家向けに、簡易加工機器やパッケージデザイン支援を提供する。"
     "地方の小さな事業者の6次産業化を後押しする。", 1, 3, 2),
    ("スポーツ・健康増進向けの地域特化型用品の開発",
     "地域のスポーツクラブや自治体と連携し、市民の健康増進に役立つ用具や用品を開発する。"
     "地域の健康づくりと製造業の新規需要開拓を両立する。", 1, 3, 1),
    ("横浜の海洋資源を活かした水産加工品のブランド化",
     "近海の水産物を使った高付加価値の加工食品を開発し、ブランドとして販売する。"
     "水産業の振興と地域の食文化の発信につなげる。", 1, 4, 1),
    ("地方創生ファンドとの連携による新事業の共同出資",
     "自治体や地域金融機関のファンドと連携し、地方創生に資する新事業に投資・参画する。"
     "資金とノウハウを提供し、地域の起業・新規事業を支援する。", 2, 3, 2),
    ("地域の介護・福祉施設向けカスタマイズ製品の開発",
     "介護施設や保育所のニーズに合わせた家具・備品を開発・納入する。"
     "地域の福祉現場の声を反映し、使いやすさと耐久性を両立した製品を提供する。", 0, 4, 1),
    ("オンライン販売と地方発送拠点の一体化モデル",
     "横浜の製造拠点から、ECサイトを通じて全国へ直接発送する体制を構築する。"
     "中間流通を簡素化し、消費者への価格還元と地域雇用の維持を両立する。", 1, 4, 2),
    ("地域の学校・教育機関向け教材・教具の開発",
     "地域の歴史や産業を学ぶための教材キットや体験用教具を開発し、学校に提供する。"
     "教育と地域の結びつきを強め、次世代の地域理解を深める。", 1, 3, 1),
    ("横浜の多文化共生を活かした輸入・輸出のハブ機能",
     "在日外国人コミュニティとの連携により、母国のニーズに合った商品を開発・輸出する。"
     "横浜の国際性を強みに、多文化市場への進出を図る。", 2, 3, 2),
    ("地域の飲食店と連携した業務用調味料・食材の開発",
     "地元の飲食店のレシピや要望を反映した業務用調味料・食材を共同開発する。"
     "地域の食の魅力向上と、製造業の新たな顧客開拓を同時に実現する。", 0, 4, 1),
    ("地方の中小製造業同士の共同受注・共同出荷プラットフォーム",
     "横浜を拠点に、複数の中小製造業が共同で大型受注に対応する仕組みを構築する。"
     "単独では難しい規模の仕事に取り組み、地域全体の受注力を高める。", 1, 4, 2),
    ("地域の障がい者スポーツ支援製品の開発・寄贈",
     "パラスポーツや障がい者スポーツに必要な用具を開発し、地域のクラブに寄贈・提供する。"
     "地域の包摂性の向上と、社会的使命の遂行を両立する。", 2, 4, 2),
    ("横浜の夜景・景観をモチーフにした記念品・ギフトの開発",
     "みなとみらいや赤レンガ倉庫など、横浜の景観をデザインに取り入れたギフト商品を開発する。"
     "観光客や法人ギフト需要を取り込み、地域の魅力を発信する。", 0, 4, 0),
    ("地域の災害備蓄向け長期保存食品の開発と供給",
     "自治体や地域の備蓄ニーズに応じた長期保存可能な食品を開発・供給する。"
     "地域の防災力向上に貢献し、平常時の地域との信頼関係を構築する。", 1, 4, 2),
    ("地方の若手経営者・起業家とのマッチング・メンタリング事業",
     "地域の若手経営者や起業希望者に対し、製造業の知見を活かしたメンタリングや協業機会を提供する。"
     "地域の次世代リーダー育成と、自社のイノベーションにつなげる。", 2, 3, 2),
]


class Command(BaseCommand):
    help = "【再現】横浜市製造業×地方創生の課題（30解決案・人間の評価を再現）を作成"

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
                tpl = PROPOSAL_TEMPLATES[j]
                conclusion, reasoning = tpl[0], tpl[1]
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
                for idx, prop in enumerate(proposals):
                    if prop.proposer_id == evaluator.id:
                        continue
                    inn, ins = PROPOSAL_TEMPLATES[idx][2], PROPOSAL_TEMPLATES[idx][3]
                    ev, score = _get_innovation_eval(inn, prop.id, evaluator.id)
                    iscore = _get_insight_score(ins, prop.id, evaluator.id)
                    ProposalEvaluation.objects.get_or_create(
                        proposal=prop,
                        evaluator=evaluator,
                        defaults={
                            "evaluation": ev,
                            "score": score,
                            "insight_level": str(iscore),
                            "insight_score": iscore,
                        },
                    )
                UserEvaluationCompletion.objects.update_or_create(
                    challenge=challenge,
                    user=evaluator,
                    defaults={"has_completed_all_evaluations": True, "completed_at": now},
                )

            commenters_pool = [u for u in proposers_for_proposals if u.id != proposer_1.id][:20]
            period_duration = (edit_deadline - start).total_seconds()
            reasonings = [
                "横浜の製造業と地方創生について、貴重な視点だと思います。",
                "地域連携の具体案として興味深いです。実装のポイントを教えてください。",
                "他地域でも類似の取り組みを聞いたことがあります。横浜ならではの強みを活かせそうですね。",
            ]
            for idx, prop in enumerate(proposals):
                impact_tier = PROPOSAL_TEMPLATES[idx][4]
                n_comments = _get_comment_count(impact_tier, prop.id)
                for k in range(n_comments):
                    c = commenters_pool[(prop.id + k) % len(commenters_pool)]
                    ratio = _get_comment_timing_ratio(impact_tier, prop.id, k, n_comments)
                    ct = start + timedelta(seconds=int(period_duration * ratio))
                    if ct > edit_deadline:
                        ct = edit_deadline - timedelta(minutes=1)
                    comm = ProposalComment.objects.create(
                        proposal=prop,
                        commenter=c,
                        target_section="reasoning",
                        conclusion="参考になりました",
                        reasoning=reasonings[(prop.id + k) % len(reasonings)],
                        is_deleted=False,
                    )
                    ProposalComment.objects.filter(pk=comm.pk).update(created_at=ct)

            ref_candidates = [i for i, t in enumerate(PROPOSAL_TEMPLATES) if t[3] >= 4]
            ref_indices = ref_candidates[:4] if len(ref_candidates) >= 4 else [3, 8, 15, 22]
            for idx in ref_indices:
                if idx < len(proposals):
                    prop = proposals[idx]
                    comments = list(ProposalComment.objects.filter(proposal=prop, is_deleted=False)[:2])
                    for comm in comments:
                        ProposalEditReference.objects.get_or_create(proposal=prop, comment=comm)

            self.stdout.write(
                self.style.SUCCESS(f"課題 {challenge.id} 作成: {challenge.title[:50]}... ({len(proposals)}件)")
            )

            if not options.get("skip_analysis"):
                try:
                    ChallengeAnalyzer(challenge.id).analyze_challenge()
                    self.stdout.write(self.style.SUCCESS(f"分析完了: 課題 {challenge.id}"))
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"分析エラー: {e}"))

        post_save.connect(analytics_signals.auto_analyze_on_challenge_close, sender=Challenge)
        self.stdout.write(self.style.SUCCESS(f"完了: 課題ID {challenge.id}"))
