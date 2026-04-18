"""
contributor_1 による課題「生成AIが与える2026年の労働市場への影響」を
50人選出で作成し、選出された50人それぞれが1件ずつ解決案を提出した状態にする。
匿名名確認用。
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from decimal import Decimal

from challenges.models import Challenge, calculate_phase_deadlines
from challenges.views import calculate_reward_amount
from selections.services import SelectionService
from selections.models import ChallengeUserAnonymousName
from proposals.models import Proposal

User = get_user_model()

TITLE = "生成AIが与える2026年の労働市場への影響"
DESCRIPTION = """2026年における生成AI（大規模言語モデル、画像生成AI等）の労働市場への影響について、
ポジティブ・ネガティブの両面から、具体的な業種・職種への影響、スキルの再定義、
新しい雇用形態の可能性などを踏まえた解決策・提言を募集します。"""

# 50件分のサンプル解決案（結論・推論）のテンプレート
PROPOSAL_TEMPLATES = [
    ("リカレント教育の義務化", "生成AIにより単純作業が代替される一方、創造性や対人スキルが重要になる。企業と行政が連携し、労働者が定期的にスキルアップデートできる制度を整備すべき。"),
    ("ユニバーサルベーシックインカムの段階的導入", "雇用の変動が激しくなる中、生活のセーフティネットとしてUBIを検討。まずは一定条件でパイロット実施し、効果を検証する。"),
    ("AI監査・説明責任の強化", "AIによる人事評価や採用判断の透明性を確保。アルゴリズムの監査と人権侵害の防止を法制度化する。"),
    ("フレキシブルワークの法制化", "リモート・ハイブリッドが標準となり、居住地と職場の紐づけが弱まる。労働法を働き方の多様化に合わせて改正する。"),
    ("デジタルスキル教育の無償化", "学校教育・職業訓練において、AIを活用するスキルを必修化。企業の再訓練費用への税制優遇も検討する。"),
    ("創造的職業の保護・振興", "AIが苦手とする芸術・介護・教育等の分野への人材流動を促進。賃金・待遇の改善で就業意欲を高める。"),
    ("ギグエコノミー労働者保護", "プラットフォーム労働者の社会保険加入、最低賃金保証、解雇規制を強化する。"),
    ("AIと人間の協働モデル構築", "完全代替ではなく補完関係を前提に、役割分担のガイドラインを業界ごとに策定する。"),
    ("中小企業へのAI導入支援", "大企業との格差を防ぐため、国がAIツール導入補助金やコンサルティングを提供する。"),
    ("労働時間の再定義", "AIによる生産性向上を賃金・労働時間に反映。週4日制や時短の拡大を社会的に議論する。"),
    ("リスキリング補助金の拡充", "失業者が新分野で再就職する際の教育費を公的に負担。キャリアチェンジを促進する。"),
    ("AI倫理委員会の設置", "労働市場へのAI導入について、労使学の専門家が議論する常設機関を設置する。"),
    ("若年層のインターンシップ義務化", "学校と企業の連携を強化し、AI時代の仕事体験を早期に提供する。"),
    ("在宅ワークの税制・社会保険統一", "リモート労働者の居住地と企業所在地の課税・保険の扱いを明確化する。"),
    ("AIによるマッチング精度向上", "求人と求職者のAIマッチングを公共職業安定所に導入し、ミスマッチを減らす。"),
    ("生産性向上の分配制度", "AI導入で生じた利益を従業員に還元する仕組みを、企業の報告義務として導入する。"),
    ("高齢者のデジタルリテラシー支援", "シニア層がAIツールを使えるよう、地域の公民館等で無料講座を実施する。"),
    ("職業訓練のオンデマンド化", "オンラインで好きな時間に学べる公的職業訓練プログラムを拡充する。"),
    ("起業支援の強化", "AIを活用した個人事業主・スタートアップへの融資・メンタリングを充実させる。"),
    ("データ労働者の権利保護", "AI学習用データの作成に従事する労働者の対価と著作権を明確にする。"),
    ("業界横断的人材の育成", "単一専門ではなく、複数分野の知識を持つT字型人材を大学・企業で育成する。"),
    ("AI医療・介護の規制と普及", "医療・介護分野でのAI利用ガイドラインを整備しつつ、効率化を進める。"),
    ("地方創生とリモートワーク", "地方自治体が移住者向けにインフラと仕事をセットで提供するモデルを拡大する。"),
    ("最低賃金の段階的引き上げ", "AIによる生産性向上を背景に、全国加重平均の引き上げペースを加速する。"),
    ("副業・兼業の促進", "本業以外の収入源を持つことを推奨し、税制・社会保険の障壁を下げる。"),
    ("STEM教育の早期開始", "小学校段階からプログラミング・データリテラシーを必修とし、裾野を広げる。"),
    ("AIによる需要予測の共有", "業界団体がAI予測を共有し、人材不足・過剰を事前に調整する。"),
    ("ワークライフインテグレーション", "仕事と生活の境界が曖昧になる中、オフラインの権利を法的に保障する。"),
    ("社会人大学院の学費補助", "キャリア途中で専門性を高める社会人への学費支援を拡大する。"),
    ("障害者雇用とAI支援", "AIの音声認識・翻訳等を活用し、障害者の就労機会を拡大する。"),
    ("インダストリー4.0人材育成", "製造業のデジタル化に対応した人材を、企業と高専・大学が連携して育成する。"),
    ("ライフシフト支援", "人生100年時代を見据え、中年期のキャリアチェンジを支援する公的プログラムを強化する。"),
    ("AIと雇用の影響評価義務", "大企業がAI導入前に雇用への影響を評価し、報告する義務を導入する。"),
    ("グローバル人材の受け入れ", "AI人材等の外国人人材の就労ビザを緩和し、日本の競争力を維持する。"),
    ("アントレプレナー教育の必修化", "大学・専門学校で起業論・イノベーション論を必修科目にする。"),
    ("同一労働同一賃金の徹底", "正規・非正規、雇用形態を問わず、同一価値労働には同一報酬を適用する。"),
    ("育児・介護と就労の両立支援", "AIによる業務効率化を活かし、短時間正社員等の柔軟な雇用形態を普及させる。"),
    ("官民データ連携", "労働市場の需給データを官民で共有し、政策と企業戦略の精度を高める。"),
    ("シニア再雇用の拡大", "65歳以上も活躍できる職種・環境を整備し、年金支給開始年齢の引き上げに対応する。"),
    ("AIによる学習パーソナライズ", "公教育にAIを導入し、児童・生徒一人ひとりに最適化された学習を提供する。"),
    ("サイバーセキュリティ人材の育成", "AI時代に増大するセキュリティリスクに対応する人材を戦略的に育成する。"),
    ("地方公務員のデジタル化", "自治体の業務をAIで効率化し、住民サービス向上と人材不足解消を両立する。"),
    ("グリーン雇用の創出", "脱炭素とAIの両立により、新たなグリーン×デジタル人材需要に対応する。"),
    ("メンタルヘルス支援の強化", "働き方の急激な変化に対応し、企業のメンタルヘルス対策を義務化・標準化する。"),
    ("ダイバーシティ推進", "多様なバックグラウンドの労働者がAI時代に活躍できるよう、採用・評価の見直しを促進する。"),
    ("産学連携の強化", "大学の研究シードと企業のニーズをマッチングするプラットフォームを国が整備する。"),
    ("労働組合の役割見直し", "新しい雇用形態に対応した労使交渉の枠組みを、労組と経営側で再構築する。"),
    ("AIツールの無料提供", "中小零細企業向けに、国がAIツールのライセンス費用を補助する。"),
    ("職業資格の見直し", "AI時代に不要になった資格を整理し、新たに必要な資格を創設する。"),
    ("女性活躍とAI", "AIによる在宅・柔軟勤務の普及で、女性の就労率向上を後押しする。"),
    ("農業・一次産業のDX", "AI・IoTを活用したスマート農業により、人手不足を解消しつつ収益性を高める。"),
    ("建設業の3K脱却", "AI・ロボットによる危険作業の代替と、若年層へのキャリア訴求を両立する。"),
    ("観光業の多言語AI", "訪日客増加に備え、AI翻訳・案内で多言語対応の労働負担を軽減する。"),
    ("金融・法務のAI活用", "定型業務のAI化により、専門家が高度な判断に集中できる環境を整える。"),
]


class Command(BaseCommand):
    help = 'contributor_1で「生成AIが与える2026年の労働市場への影響」を50人選出・50件の解決案で作成'

    def handle(self, *args, **options):
        # contributor_1 を取得
        try:
            contributor = User.objects.get(username='contributor_1', user_type='contributor')
        except User.DoesNotExist:
            self.stderr.write(self.style.ERROR('contributor_1 が見つかりません。'))
            return

        required_count = 50
        total_days = 6  # 最低6日
        now = timezone.now()
        deadline = now + timezone.timedelta(days=total_days)
        deadline = deadline.replace(hour=23, minute=59, second=59, microsecond=999999)

        with transaction.atomic():
            # 報酬計算
            reward_amount = Decimal(str(calculate_reward_amount(required_count)))
            adoption_reward = Decimal('500000')  # 50万円

            proposal_deadline, edit_deadline, evaluation_deadline = calculate_phase_deadlines(now, total_days)

            challenge = Challenge.objects.create(
                title=TITLE,
                description=DESCRIPTION,
                contributor=contributor,
                reward_amount=reward_amount,
                adoption_reward=adoption_reward,
                required_participants=required_count,
                deadline=deadline,
                proposal_deadline=proposal_deadline,
                edit_deadline=edit_deadline,
                evaluation_deadline=evaluation_deadline,
                status='open',
            )
            self.stdout.write(self.style.SUCCESS(f'課題を作成しました: {challenge.id} {challenge.title}'))

            # 50人選出
            selection = SelectionService.random_selection(challenge, required_count)
            selected_users = list(selection.selected_users.all())
            self.stdout.write(self.style.SUCCESS(f'50人選出完了。実際の選出人数: {len(selected_users)}'))

            # 50件の解決案を作成
            created = 0
            for i, user in enumerate(selected_users):
                conclusion, reasoning = PROPOSAL_TEMPLATES[i % len(PROPOSAL_TEMPLATES)]

                try:
                    cuan = ChallengeUserAnonymousName.objects.get(challenge=challenge, user=user)
                    anonymous_name = cuan.anonymous_name
                except ChallengeUserAnonymousName.DoesNotExist:
                    anonymous_name = None

                Proposal.objects.create(
                    challenge=challenge,
                    proposer=user,
                    conclusion=conclusion,
                    reasoning=reasoning,
                    anonymous_name=anonymous_name,
                    is_anonymous=True,
                    status='submitted',
                )
                created += 1

            self.stdout.write(self.style.SUCCESS(f'{created}件の解決案を作成しました'))
            self.stdout.write(f'課題ID: {challenge.id}, 期限: {deadline}')
