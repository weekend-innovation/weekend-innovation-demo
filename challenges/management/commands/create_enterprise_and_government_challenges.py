"""
【企業向け】と【自治体向け】の課題を各1件、解決案を約30件ずつ作成。

- 【企業向け】DX推進のための組織変革をどう進めるか（約30件の解決案）
- 【自治体向け】住民サービスの満足度を上げるにはどうすればよいか（約30件の解決案）

期限は評価期限を 2026年2月27日 23:59 にし、結果画面が表示されるようにする。
created_at を 2026-02-20 に設定し、ソートで一番上に来やすくする。
"""
from datetime import datetime, timedelta
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


# 【企業向け】DX推進のための組織変革（結論, 理由, innovation_level, insight_level, impact_tier）
ENTERPRISE_PROPOSALS = [
    ("経営層がDXを経営戦略の柱として宣言し、予算とKPIを明確に割り当てる",
     "トップのコミットがないと部門間の連携が進まない。経営層が宣言し、予算とKPIを設定することで推進力を担保する。", 0, 4, 1),
    ("DX推進室を設置し、各部門から兼務・専任のキーパーソンを集める",
     "横断的な推進組織を置くことで、部門の縦割りを超えた施策を実行できる。兼務と専任のバランスで実務と権限を両立する。", 0, 4, 1),
    ("ペーパーレス・電子稟議を全社一律で導入し、業務プロセスのデジタル化を進める",
     "稟議・承認の電子化で業務スピードを上げ、データが蓄積される土台をつくる。全社一律で運用ルールを統一する。", 0, 4, 1),
    ("クラウド基盤とセキュリティポリシーを先に整備し、その上でアプリを展開する",
     "基盤がバラバラだと後から統合コストが膨らむ。クラウドとセキュリティを先に整え、その上で業務アプリを展開する。", 0, 4, 1),
    ("データガバナンスとデータドリブン意思決定のためのダッシュボードを全社展開する",
     "データの定義・品質・アクセス権を整備し、経営・現場が同じ指標を見て意思決定できるダッシュボードを導入する。", 1, 4, 2),
    ("デジタル人材の採用・リカレント教育を強化し、内製化の土台をつくる",
     "外部依存を減らすため、採用と社内研修でデータ・開発スキルを持つ人材を増やし、内製化を進める。", 0, 4, 1),
    ("RPA・業務自動化のPoCを各部門で実施し、成功事例を横展開する",
     "小さい単位でPoCを実施し、効果が出たものから横展開。現場の負担を減らしつつ、DXの実感を広げる。", 0, 4, 1),
    ("顧客接点のデジタル化（EC・CRM・チャット）を優先し、収益に直結する領域から着手する",
     "売上・顧客満足に直結する領域からデジタル化し、効果を可視化して社内の理解を得る。", 0, 4, 1),
    ("アジャイル・DevOpsの開発体制を導入し、スピードと品質を両立する",
     "ウォーターフォールからアジャイルに移行し、DevOpsでリリースを短縮。変化に強い開発体制をつくる。", 1, 4, 2),
    ("サプライチェーン・調達のデジタル化で可視化と効率化を同時に進める",
     "調達・在庫・物流をデジタル化し、可視化と効率化でコスト削減とリスク低減を図る。", 0, 4, 1),
    ("AI・機械学習を業務の属人化解消と品質向上に活用する",
     "定型判断や予測をAIで補助し、属人化を減らしつつ品質を安定させる。まずは効果が出やすい領域から導入する。", 1, 4, 2),
    ("働き方改革とDXを一体で推進し、リモート・フレックス前提の業務設計にする",
     "リモート・フレックスを前提にツールとプロセスを設計し、働き方改革とDXを同時に進める。", 0, 4, 1),
    ("顧客ジャーニーを可視化し、デジタルとリアルの接点を最適化する",
     "顧客の行動を可視化し、タッチポイントごとにデジタルとリアルの役割を決めて体験を改善する。", 1, 4, 2),
    ("サイバーセキュリティとBCPを強化し、リスクを抑えながらデジタル化を進める",
     "セキュリティとBCPを強化した上でデジタル化を進め、リスクを許容可能な範囲に抑える。", 0, 4, 1),
    ("オープンイノベーション・スタートアップ連携で外部の知見を取り込む",
     "自社だけではスピードが足りない領域は、スタートアップや大学と連携し、知見とスピードを取り込む。", 2, 4, 2),
    ("DXロードマップを策定し、短期・中期・長期の目標と投資を明示する",
     "経営と現場で共有するロードマップを策定し、何をいつまでにやるかを明示して合意形成する。", 0, 4, 1),
    ("チャネル別の顧客データを統合し、オムニチャネルで体験を一元化する",
     "Web・店舗・問い合わせのデータを統合し、顧客ごとに一貫した体験を提供できるようにする。", 1, 4, 2),
    ("デジタルツインで製造・物流のシミュレーションをし、意思決定を前倒しする",
     "製造・物流をデジタル上で再現し、シミュレーションで意思決定の質とスピードを上げる。", 2, 3, 2),
    ("従業員体験（EX）をデジタルで改善し、採用・定着・生産性を上げる",
     "入社から退職までの体験をデジタルでスムーズにし、満足度と生産性を高める。", 0, 4, 1),
    ("規制・コンプライアンス対応をデジタル化し、リスクと工数を削減する",
     "法務・内部統制のプロセスをデジタル化し、対応工数を減らしつつリスクを管理する。", 0, 3, 1),
    ("API・データ連携でサプライヤー・パートナーとリアルタイム連携する",
     "APIでサプライヤーやパートナーとデータ連携し、納期・在庫・品質をリアルタイムで把握する。", 1, 4, 2),
    ("デジタルマーケティングとMAを強化し、リード獲得から成約までを可視化する",
     "マーケティングオートメーションと分析で、リードから成約までの経路を可視化し、施策を最適化する。", 0, 4, 1),
    ("現場の声を収集する仕組みと改善サイクルをデジタルで回す",
     "現場の提案・不満をデジタルで収集し、改善サイクルを回して現場主導の変革を促す。", 0, 4, 1),
    ("経営会議・部門会議をデータドリブンにし、KPIとアクションを紐付ける",
     "会議でKPIとアクションを紐付け、データに基づく議論とフォローを標準化する。", 0, 4, 0),
    ("顧客サポートのチャットボット・FAQで一次対応を自動化し、人的リソースを有効活用する",
     "定型問い合わせをボットとFAQで対応し、人が対応すべき案件に集中できるようにする。", 0, 4, 1),
    ("HRテックで採用・評価・育成を可視化し、人材戦略とDXを連動させる",
     "採用から評価・育成までをシステムで可視化し、人材配置と育成計画をデータで最適化する。", 1, 4, 2),
    ("既存システムのAPI化・マイクロサービス化でレガシーを段階的に刷新する",
     "一括リプレースを避け、API化・マイクロサービス化で段階的にレガシーを刷新し、リスクを分散する。", 1, 4, 2),
    ("デジタルリテラシー研修を階層別に実施し、全員がツールとデータを活用できるようにする",
     "経営・管理職・一般社員それぞれに合ったリテラシー研修を実施し、デジタル活用の土台をつくる。", 0, 4, 0),
    ("PoC・パイロットの成功・失敗を社内で共有し、学習する文化をつくる",
     "PoCの結果を隠さず共有し、失敗から学ぶ文化をつくることで、挑戦と学習を繰り返せるようにする。", 0, 4, 1),
    ("外部ベンダーとSLA・ガバナンスを明確にし、内製と外注の役割分担を最適化する",
     "ベンダーとのSLAとガバナンスを明確にし、内製と外注の役割分担を決めてスピードと品質を両立する。", 0, 3, 1),
    ("経営ダッシュボードでKPIをリアルタイム共有し、意思決定のスピードを上げる",
     "経営層が参照するKPIダッシュボードを整備し、データに基づく意思決定を日常化する。", 0, 4, 1),
]

# 【自治体向け】住民サービスの満足度向上（結論, 理由, innovation_level, insight_level, impact_tier）
GOVERNMENT_PROPOSALS = [
    ("窓口業務のワンストップ化と予約・案内のデジタル化で待ち時間を削減する",
     "窓口を統合し、予約・案内をWebで行うことで待ち時間を減らし、来庁の負担を軽減する。", 0, 4, 1),
    ("オンライン申請・電子証明を拡充し、自宅から手続きできるサービスを増やす",
     "高頻度の手続きをオンライン申請で完結できるようにし、窓口来庁が不要な選択肢を増やす。", 0, 4, 1),
    ("住民向けポータル・アプリで各種お知らせ・申請・問い合わせを一元化する",
     "住民が一つのサイト・アプリでお知らせ・申請・問い合わせにアクセスできるようにする。", 1, 4, 2),
    ("窓口・コールセンターの対応品質を統一するマニュアルと研修を実施する",
     "対応のばらつきを減らすため、マニュアルと研修で品質を統一し、どの窓口でも同じ水準のサービスを提供する。", 0, 4, 1),
    ("住民満足度調査を定期実施し、結果を公表して改善サイクルに活かす",
     "満足度調査で住民の声を継続的に収集し、結果を公表して改善施策に反映する。", 0, 4, 1),
    ("高齢者・障害者向けに窓口のバリアフリーと訪問対応を強化する",
     "窓口のバリアフリー化と、訪問による手続き支援を強化し、誰もが利用しやすいサービスにする。", 0, 4, 1),
    ("子育て・介護・防災などテーマ別の相談窓口をワンストップで提供する",
     "テーマ別の相談を一つの窓口で受け付け、必要な部署につなぐワンストップ窓口を設ける。", 0, 4, 1),
    ("多言語・やさしい日本語対応を拡充し、外国人住民にも分かりやすい案内にする",
     "多言語とやさしい日本語の案内・窓口対応を拡充し、言語の壁で不利益が出ないようにする。", 0, 4, 1),
    ("開庁時間外・土日対応の窓口やオンライン窓口を試験的に導入する",
     "働く住民が利用しやすいよう、時間外・土日の窓口やオンライン窓口を試験的に導入する。", 1, 4, 2),
    ("申請の処理状況をオンラインで確認できるようにし、透明性を高める",
     "申請がどこまで進んでいるかをオンラインで確認できるようにし、不安と問い合わせを減らす。", 0, 4, 1),
    ("地域の民生委員・自治会と連携し、困りごとを早期に把握・つなぐ体制をつくる",
     "民生委員・自治会と情報共有し、住民の困りごとを早く把握して適切なサービスにつなぐ。", 0, 4, 1),
    ("防災・緊急時の情報発信をSNS・アプリ・メールで多チャネル化する",
     "災害時などに情報が届きやすいよう、SNS・アプリ・メールなど複数チャネルで発信する。", 0, 4, 1),
    ("公共施設の予約・利用をオンライン化し、利便性と公平性を高める",
     "公民館・体育館などの予約をオンライン化し、申し込みの手間を減らし、公平に利用できるようにする。", 0, 4, 1),
    ("住民相談の記録を共有し、窓口を替えても継続した対応ができるようにする",
     "相談内容を安全に共有し、担当が変わっても継続した対応ができるようにする。", 0, 4, 1),
    ("地域のイベント・講座・ボランティア情報を一覧できるサイトを運営する",
     "地域の活動情報を一覧できるサイトを運営し、参加のハードルを下げる。", 0, 3, 1),
    ("ペーパーレス・電子申請の推進で、窓口と住民双方の負担を減らす",
     "紙の申請を減らし、電子申請を推進することで、窓口の作業負荷と住民の手間の両方を減らす。", 0, 4, 1),
    ("住民向けの説明会・意見聴取をオンラインでも実施し、参加の選択肢を増やす",
     "説明会やパブリックコメントをオンラインでも実施し、参加しやすい形を増やす。", 0, 4, 1),
    ("子育て・教育・就労などライフステージ別の情報をまとめて提供する",
     "ライフステージに応じた情報をまとめて提供し、住民が自分に必要な情報を見つけやすくする。", 0, 4, 1),
    ("窓口の混雑状況をWebで公開し、来庁のタイミングを選びやすくする",
     "混雑状況をリアルタイムで公開し、住民が空いている時間に来庁できるようにする。", 1, 4, 1),
    ("職員のサービス志向を高めるための研修と評価制度を導入する",
     "住民目線のサービスを評価し、研修と人事評価に反映することで、職員の意識と行動を変える。", 0, 4, 1),
    ("地域の課題を住民と一緒に考えるワークショップ・協働の場を定期開催する",
     "住民と行政が一緒に課題を話し合う場を定期開催し、ニーズの把握と合意形成を進める。", 1, 4, 2),
    ("証明書のコンビニ交付・郵送対応を拡大し、取得の利便性を高める",
     "コンビニ交付・郵送で証明書を取得できるサービスを拡大し、窓口に来られない住民の負担を減らす。", 0, 4, 1),
    ("住民票・戸籍等の手続きをオンラインで完結できる範囲を段階的に拡大する",
     "可能な手続きからオンライン化し、住民が自宅等から手続きできる選択肢を増やす。", 0, 4, 1),
    ("苦情・クレームを分析し、業務改善と再発防止に活かす仕組みをつくる",
     "苦情を記録・分析し、業務改善と再発防止策に活かす仕組みをつくる。", 0, 4, 0),
    ("地域の医療・介護・福祉の情報を一元的に案内する窓口・サイトを整備する",
     "医療・介護・福祉の情報を一つの窓口・サイトで案内し、必要なサービスにたどり着きやすくする。", 0, 4, 1),
    ("デジタルデバイド対策として、窓口でのデジタル支援・代行を充実させる",
     "デジタルが苦手な住民向けに、窓口での操作支援や代行を充実させ、格差を広げないようにする。", 0, 4, 1),
    ("住民満足度の目標値を設定し、年度ごとに改善計画を立てて実行・検証する",
     "満足度の目標を設定し、改善計画を立てて実行し、毎年検証して次の改善に活かす。", 0, 4, 1),
    ("子育て世帯・若者向けの情報発信と相談窓口を強化する",
     "子育て・転入・就職など若い世代のニーズに合わせた情報と相談窓口を強化する。", 0, 4, 1),
    ("公共施設・公園の予約・利用状況を可視化し、公平で使いやすい仕組みにする",
     "施設の利用状況を可視化し、予約の公平性と使いやすさを両立する。", 0, 3, 1),
    ("職員の業務負荷を可視化し、窓口の体制と人員配置を最適化する",
     "業務量と負荷を可視化し、ピーク時やテーマ別の人員配置を最適化して待ち時間と品質を改善する。", 0, 4, 1),
]

CHALLENGE_ENTERPRISE = {
    "title": "【企業向け】DX推進のための組織変革をどう進めるか",
    "description": (
        "デジタル変革（DX）を進めたいが、どこから手を付ければよいか、組織の抵抗感をどう乗り越えるかで悩んでいる企業向けの課題です。"
        "経営戦略・組織体制・ツール導入・人材・文化など、多様な視点から具体的な解決策を募集します。"
    ),
    "templates": ENTERPRISE_PROPOSALS,
}

CHALLENGE_GOVERNMENT = {
    "title": "【自治体向け】住民サービスの満足度を上げるにはどうすればよいか",
    "description": (
        "住民サービスの満足度向上を目指す自治体向けの課題です。"
        "窓口の利便性、オンライン化、情報発信、相談体制、職員の対応力など、"
        "多様な視点から具体的な解決策を募集します。"
    ),
    "templates": GOVERNMENT_PROPOSALS,
}


class Command(BaseCommand):
    help = "【企業向け】と【自治体向け】の課題を各1件、解決案を約30件ずつ作成（期限2月27日・結果画面表示用）"

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

        # 評価期限を 2026年2月27日 23:59 にし、結果画面が出るようにする。ソートで一番上に来るよう start を 2026-02-20 に設定。
        start = timezone.make_aware(datetime(2026, 2, 20, 0, 0, 0))
        total_days = 7
        proposal_deadline, edit_deadline, evaluation_deadline = calculate_phase_deadlines(start, total_days)
        deadline = evaluation_deadline
        reward_amount = Decimal(str(calculate_reward_amount(required_count)))
        adoption_reward = Decimal("500000")

        created_ids = []

        for challenge_def in (CHALLENGE_ENTERPRISE, CHALLENGE_GOVERNMENT):
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
                selection.completed_at = timezone.now()
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
                        defaults={"has_completed_all_evaluations": True, "completed_at": timezone.now()},
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
                    self.style.SUCCESS(f"課題 {challenge.id} 作成: {challenge_def['title'][:50]}... ({len(proposals)}件)")
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
