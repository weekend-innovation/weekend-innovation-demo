"""
例1（自治体向け・観光地来訪者増加）と例2（企業向け・リモートワーク定着）の課題・解決案を作成。

- 例1: 観光地の来訪者を3年で2割増やすにはどうすればよいか
  想定クラスタ: インフラ・アクセス改善 / SNS・PR施策 / 地元住民との協働・体験コンテンツ
- 例2: リモートワーク定着率を上げるために何を優先すべきか
  想定クラスタ: ツール・環境整備 / 評価・人事制度の見直し / コミュニケーション設計

各課題20件程度の解決案。評価・コメントは再現用と同様に付与。
"""
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


def _get_innovation_eval(innovation_level: int, prop_id: int, evaluator_id: int) -> tuple:
    x = (prop_id + evaluator_id) % 20
    if innovation_level == 0:
        return ("yes", 0) if x < 15 else (("maybe", 1) if x < 19 else ("no", 2))
    if innovation_level == 1:
        return ("yes", 0) if x % 4 == 0 else (("maybe", 1) if x % 4 in (1, 2) else ("no", 2))
    return ("yes", 0) if x == 0 else (("maybe", 1) if x <= 3 else ("no", 2))


def _get_insight_score(insight_level: int, prop_id: int, evaluator_id: int) -> int:
    offset = (prop_id + evaluator_id) % 3 - 1
    return max(1, min(5, insight_level + offset))


def _get_comment_count(impact_tier: int, prop_id: int) -> int:
    if impact_tier == 0:
        return 2 + (prop_id % 3)
    if impact_tier == 1:
        return 4 + (prop_id % 3)
    return 6 + (prop_id % 4)


def _get_comment_timing_ratio(impact_tier: int, prop_id: int, k: int, total: int) -> float:
    if impact_tier == 0:
        return 0.2 + 0.3 * (k / max(1, total))
    if impact_tier == 1:
        return 0.3 + 0.4 * (k / max(1, total))
    return 0.5 + 0.5 * (k / max(1, total))


# 例1: 自治体向け「観光地の来訪者増加」 (結論, 理由, innovation_level, insight_level, impact_tier)
# クラスタ: インフラ・アクセス改善 / SNS・PR施策 / 地元住民との協働・体験コンテンツ
TOURISM_PROPOSALS = [
    # インフラ・アクセス改善
    ("駐車場の増設と予約制導入で混雑を分散し、来訪のハードルを下げる",
     "観光地の来訪者減少の一因はアクセスの不便さ。駐車場を増設し、予約制にすることで渋滞を減らし、スムーズな来訪を実現する。", 0, 4, 1),
    ("公共交通の本数増便と周遊バスの新設で車なしでも回れるようにする",
     "鉄道・バスの本数増加と、主要スポットを結ぶ周遊バスを運行。環境負荷を抑えつつ、来訪者数を増やす。", 0, 4, 1),
    ("主要駅から観光地までの直通シャトルバスを運行する",
     "最寄り駅から観光地まで直結するシャトルバスを整備。乗り換えの手間を減らし、来訪の利便性を高める。", 0, 4, 0),
    ("観光地周辺の道路整備と案内看板の充実",
     "道幅の確保や案内看板の多言語対応により、初めての来訪者でも迷いにくくする。", 0, 4, 1),
    ("無料WiFiと多言語対応のデジタル案内を観光地全体に展開する",
     "観光地全域に無料WiFiを整備し、多言語対応のデジタルマップや音声ガイドを提供。情報アクセスを改善する。", 1, 4, 1),
    ("駐輪場の整備とレンタサイクル拠点の拡大",
     "自転車で回れる範囲を広げ、駐輪場とレンタサイクル拠点を増やす。環境に優しく、滞在時間の延伸にもつながる。", 0, 3, 1),
    ("バリアフリー化とベビーカー・車椅子の貸出体制の強化",
     "段差解消やエレベーター設置、ベビーカー・車椅子の貸出で、多様な来訪者が訪れやすくする。", 0, 4, 1),
    ("観光地間の共通パス・フリーパスの発売",
     "複数施設を安価で回れる共通パスを発売。1回の来訪で複数スポットを回る動機づけとする。", 0, 4, 0),
    # SNS・PR施策
    ("インフルエンサーやメディアと連携した発信で認知を拡大する",
     "地域の魅力を発信できるインフルエンサーやメディアと連携し、SNSやテレビ・雑誌で情報を拡散する。", 0, 4, 1),
    ("Instagram・TikTok向けのフォトスポット・体験コンテンツを整備する",
     "映えるスポットや短尺動画向けの体験を用意し、SNSでシェアされやすい仕掛けを増やす。", 1, 4, 2),
    ("季節ごとのキャンペーンと限定イベントでリピートを促す",
     "桜・紅葉・雪景色など季節ごとのキャンペーンと限定イベントを実施し、リピート来訪を増やす。", 0, 4, 1),
    ("地域の特産品・ご当地グルメを軸にしたPR動画の制作・配信",
     "地域の食や特産品を前面に出した動画を制作し、YouTubeやSNSで配信。食欲を刺激するコンテンツで来訪意欲を高める。", 0, 4, 1),
    ("観光協会と連携したポータルサイト・アプリのリニューアル",
     "観光協会と連携し、イベント・施設情報が一覧できるポータルサイトやアプリを刷新。情報の見つけやすさを改善する。", 0, 3, 1),
    ("地元企業・店舗と連携したクーポン・スタンプラリーの実施",
     "地元店舗と連携したクーポンやスタンプラリーで、回遊と消費を促進する。", 0, 4, 0),
    # 地元住民との協働・体験コンテンツ
    ("地元住民がガイドをする「おらが町ツアー」の定期開催",
     "地元住民が案内するツアーを定期開催。地域の隠れた魅力や人情を伝え、体験型の来訪を増やす。", 1, 4, 2),
    ("農林漁業体験・工房体験など体験型コンテンツの拡充",
     "農作業・漁業・工房体験など、参加型のコンテンツを拡充。単なる見学ではなく、体験としての価値を高める。", 1, 4, 1),
    ("民泊・ゲストハウスと連携した滞在型観光の推進",
     "民泊やゲストハウスと連携し、ゆっくり滞在できるプランを提案。滞在日数の延伸と地域経済への波及を図る。", 1, 3, 2),
    ("地域の祭り・伝統行事を観光資源として発信し、参加型イベントにする",
     "祭りや伝統行事を観光資源として位置づけ、参加型イベントとして発信。地域文化と来訪者をつなぐ。", 0, 4, 1),
    ("地元中学生・高校生による観光案内・ウェルカム活動",
     "地元の生徒が観光案内やウェルカム活動に参加。若い視点の案内と、地域の将来世代の参画をアピールする。", 2, 4, 2),
    ("地元飲食店と連携した「ご当地ランチマップ」と食べ歩きコースの整備",
     "地元の飲食店と連携したランチマップや食べ歩きコースを整備。食を通じた回遊と地域店舗の活性化を両立する。", 0, 4, 1),
]

# 例2: 企業向け「リモートワークの定着」 (結論, 理由, innovation_level, insight_level, impact_tier)
# クラスタ: ツール・環境整備 / 評価・人事制度の見直し / コミュニケーション設計
REMOTE_PROPOSALS = [
    # ツール・環境整備
    ("在宅勤務に必要な通信環境・機器の支給・補助を全社で統一する",
     "PC・モニター・通信費の支給または補助を全社統一し、在宅でもオフィスと同等の環境を整える。", 0, 4, 1),
    ("セキュリティと利便性を両立したVPN・クラウドツールの導入",
     "VPNとクラウドツールを整備し、セキュアにどこからでもアクセスできるようにする。", 0, 4, 1),
    ("チャット・ビデオ会議・タスク管理ツールを一本化し、運用ルールを定める",
     "Slack・Teams・Zoom・Asanaなどを使い分けず、社内でツールを一本化。運用ルールを明文化して定着させる。", 0, 4, 1),
    ("在宅勤務環境整備のための一時金・リース制度の導入",
     "デスク・椅子・照明など在宅環境整備のための一時金またはリース制度を設け、従業員の負担を軽減する。", 0, 4, 0),
    ("オフィス出社と在宅のハイブリッドに対応した席・会議室の予約システム",
     "出社日は席・会議室を予約する仕組みにし、ハイブリッド勤務でもオフィスを無駄なく使えるようにする。", 1, 4, 1),
    ("情報漏洩対策を強化した端末・アクセス管理の徹底",
     "端末の暗号化・アクセスログ・DLPなど情報漏洩対策を強化し、リモートでもセキュリティを担保する。", 0, 4, 1),
    ("ITヘルプデスクの拡充と在宅サポート体制の整備",
     "在宅時のトラブルに対応できるヘルプデスクを拡充し、問い合わせ窓口とサポート体制を整える。", 0, 3, 1),
    # 評価・人事制度の見直し
    ("プロセスより成果で評価する制度に移行し、在宅・出社を問わず同一基準で評価する",
     "働く場所ではなく成果で評価する制度にし、リモートでも正当に評価されるようにする。", 1, 4, 2),
    ("リモート勤務を前提にした目標設定・OKR・1on1の運用",
     "目標設定・OKR・1on1をリモート前提で設計し、進捗とフィードバックを可視化する。", 0, 4, 1),
    ("キャリアパス・昇進においてリモート勤務を不利にしない方針を明示する",
     "昇進・キャリアパスにおいてリモート勤務を不利に扱わないことを就業規則・人事方針で明示する。", 0, 4, 1),
    ("リモートワーク定着のための研修・eラーニングを全員に義務化する",
     "リモートでの働き方・コミュニケーション・セキュリティに関する研修を全員に受けさせ、定着の土台をつくる。", 0, 4, 0),
    ("在宅勤務手当・通信費支給のルールを明確化し、不公平感をなくす",
     "在宅勤務手当や通信費の支給ルールを明確にし、不満や不公平感を減らす。", 0, 3, 1),
    ("副業・兼業を認める制度とリモート勤務の組み合わせで柔軟な働き方を推進する",
     "副業・兼業を認め、リモート勤務と組み合わせることで、働く場所・時間の柔軟性を高める。", 2, 3, 2),
    ("管理職向けにリモートチームマネジメント研修を実施する",
     "管理職向けにリモートでのマネジメント・1on1・心理的安全性の研修を実施し、現場の定着を支える。", 0, 4, 1),
    # コミュニケーション設計
    ("オンライン雑談・カジュアルミーティングの時間を週次で設ける",
     "業務以外の雑談やカジュアルな交流の時間を週次で設け、つながりと心理的安全性を保つ。", 0, 4, 1),
    ("定例の会議は原則オンラインとし、議題と時間を厳守する",
     "定例は原則オンラインに統一し、アジェンダと時間を守ることで、リモートでも参加しやすくする。", 0, 4, 0),
    ("1on1とチーム振り返りを定期的にオンラインで実施する",
     "1on1とチームの振り返りを定期的にオンラインで実施し、悩みや改善点を拾い上げる。", 0, 4, 1),
    ("社内SNS・チャットで情報共有と雑談の場を分けて運用する",
     "チャンネルやスレッドで「情報共有」と「雑談」を分け、必要な情報が流れつつ、関係性も維持できるようにする。", 0, 4, 1),
    ("リモートでも参加しやすいオフサイト・年次のリアル開催で一体感を補う",
     "四半期や年次でオフサイトやリアルイベントを開催し、リモートだけでは得にくい一体感を補う。", 1, 4, 2),
    ("「見える化」のルールを統一し、進捗・ブロッカーを共有する",
     "進捗・ブロッカー・稼働をダッシュボードや定例で共有するルールを統一し、リモートでも状況が分かるようにする。", 0, 4, 1),
]

# 課題定義: (タイトル, 説明, 提案テンプレートリスト)
CHALLENGE_1 = {
    "title": "○○市の観光地の来訪者を3年で2割増やすにはどうすればよいか",
    "description": (
        "本市の観光地では、来訪者数の伸び悩みが課題となっています。"
        "3年で来訪者を2割増やすために、インフラ整備、PR・発信、地域との協働・体験コンテンツなど、"
        "多様な視点から具体的な解決策を募集します。"
    ),
    "templates": TOURISM_PROPOSALS,
}

CHALLENGE_2 = {
    "title": "組織のリモートワーク定着率を上げるために、何を優先すべきか",
    "description": (
        "リモートワークを導入したものの、定着率や生産性に課題を感じている組織向けの課題です。"
        "ツール・環境整備、評価・人事制度の見直し、コミュニケーション設計など、"
        "何を優先し、どのように進めるべきか、具体的な解決策を募集します。"
    ),
    "templates": REMOTE_PROPOSALS,
}


class Command(BaseCommand):
    help = "例1（観光地来訪者増加）と例2（リモートワーク定着）の課題・解決案を各20件程度で作成"

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

        if len(eligible) < 40:
            self.stderr.write(self.style.ERROR(f"提案者が40人未満です（{len(eligible)}人）。"))
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

        created_ids = []

        for challenge_def in (CHALLENGE_1, CHALLENGE_2):
            templates = challenge_def["templates"]
            with transaction.atomic():
                challenge = Challenge.objects.create(
                    title=challenge_def["title"],
                    description=challenge_def["description"],
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
                ][: len(templates) - 1]

                proposals = []
                for j, proposer in enumerate(proposers_for_proposals):
                    if j >= len(templates):
                        break
                    tpl = templates[j]
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
                        if idx >= len(templates):
                            continue
                        tpl = templates[idx]
                        inn, ins = tpl[2], tpl[3]
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

                commenters_pool = [u for u in proposers_for_proposals if u.id != proposer_1.id][:15]
                period_duration = (edit_deadline - start).total_seconds()
                reasonings = [
                    "具体的で参考になりました。",
                    "実装のポイントをさらに知りたいです。",
                    "他事例との比較があるとより分かりやすいと思います。",
                ]
                for idx, prop in enumerate(proposals):
                    if idx >= len(templates):
                        continue
                    impact_tier = templates[idx][4]
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

                ref_candidates = [i for i, t in enumerate(templates) if t[3] >= 4]
                ref_indices = ref_candidates[:4] if len(ref_candidates) >= 4 else [0, 5, 10, 15]
                for idx in ref_indices:
                    if idx < len(proposals):
                        prop = proposals[idx]
                        comments = list(ProposalComment.objects.filter(proposal=prop, is_deleted=False)[:2])
                        for comm in comments:
                            ProposalEditReference.objects.get_or_create(proposal=prop, comment=comm)

                created_ids.append((challenge.id, challenge_def["title"], len(proposals)))
                self.stdout.write(
                    self.style.SUCCESS(f"課題 {challenge.id} 作成: {challenge_def['title'][:40]}... ({len(proposals)}件)")
                )

                if not options.get("skip_analysis"):
                    try:
                        ChallengeAnalyzer(challenge.id).analyze_challenge()
                        self.stdout.write(self.style.SUCCESS(f"分析完了: 課題 {challenge.id}"))
                    except Exception as e:
                        self.stderr.write(self.style.ERROR(f"分析エラー: {e}"))

        post_save.connect(analytics_signals.auto_analyze_on_challenge_close, sender=Challenge)

        for cid, title, n in created_ids:
            self.stdout.write(self.style.SUCCESS(f"  課題ID {cid}: {title} ({n}件)"))
        self.stdout.write(self.style.SUCCESS("完了"))
