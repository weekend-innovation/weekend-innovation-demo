"""
【企業向け】生成AI活用の課題を1件、解決案30件で作成。

以前作成した課題と同じ条件:
- contributor_1 を課題投稿者として使用
- proposer_1 を含む選出ユーザーで提案生成
- 期限は 2026-02-27 23:59（フェーズ締切も同一ロジック）
- created_at は 2026-02-20 に固定（一覧で上位に表示されやすくする）
- status は closed、分析実行（--skip-analysis で省略可）
"""
from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models.signals import post_save
from django.utils import timezone

from challenge_analytics import signals as analytics_signals
from challenge_analytics.services import ChallengeAnalyzer
from challenges.models import Challenge, calculate_phase_deadlines
from challenges.views import calculate_reward_amount
from proposals.models import Proposal, ProposalComment, ProposalEditReference, ProposalEvaluation
from selections.models import ChallengeUserAnonymousName, UserEvaluationCompletion
from selections.services import SelectionService

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


# (結論, 理由, innovation_level, insight_level, impact_tier)
GENAI_ENTERPRISE_PROPOSALS = [
    (
        "全社共通の生成AI利用方針と禁止事項を先に整備し、利用範囲を段階的に広げる",
        "無秩序に導入すると情報漏えいや誤情報の拡散が起きるため、まずガイドラインと承認プロセスを整えた上で、安全な領域から導入する。",
        0, 4, 1,
    ),
    (
        "営業・企画・法務などの間接部門から生成AI活用を始め、短期成果を可視化する",
        "議事録要約や資料作成支援は効果が出やすく、現場の抵抗感が低い。短期成果を示すことで製造現場への展開を進めやすくなる。",
        0, 4, 1,
    ),
    (
        "顧客対応チャットを生成AIで高度化し、一次回答を自動化してCS品質を平準化する",
        "問い合わせ量が多い領域で応答品質を均一化でき、担当者は高難度案件に集中できる。結果として応答速度と満足度が向上する。",
        0, 4, 1,
    ),
    (
        "生成AIは社外向けではなく社内ナレッジ検索に限定し、誤回答リスクを抑えて活用する",
        "社外公開用途はブランド毀損リスクが高い一方、社内文書検索なら影響範囲を管理しやすく、効果と安全性のバランスを取りやすい。",
        0, 4, 1,
    ),
    (
        "オープンモデル活用でコストを抑えつつ、機密領域はオンプレミスLLMで分離運用する",
        "全領域を高額な商用APIで賄うと費用が膨らむため、機密度に応じてモデルを使い分けることで費用対効果を最大化できる。",
        1, 4, 2,
    ),
    (
        "トップダウンではなく各部門の現場提案を公募し、採択制で生成AIユースケースを育てる",
        "現場起点の課題の方が定着しやすいため、部門横断で提案を募って小規模実験を回す方が、実運用につながる案が増える。",
        1, 4, 2,
    ),
    (
        "全社員に同一研修を行うのではなく、職種別にプロンプト設計教育を分ける",
        "営業・開発・管理部門で必要スキルが異なるため、共通研修だけでは実務活用が進まない。役割別教育で活用率を上げる。",
        0, 4, 1,
    ),
    (
        "生成AIで作成した成果物には必ず人間の最終承認を付ける運用ルールを義務化する",
        "AIの幻覚や偏りは完全に排除できないため、法務・品質・広報観点で責任を明確化するために人間承認プロセスが必要になる。",
        0, 5, 1,
    ),
    (
        "PoCを増やすより、効果が出た3領域に予算を集中して本番実装を急ぐ",
        "PoC乱立は学習効果はあるが収益化が遅れる。勝ち筋が見えた領域に資源を集中した方が全社成果につながる。",
        1, 4, 2,
    ),
    (
        "逆に本番展開を急がず、半年間はPoC専用期間として失敗事例を意図的に蓄積する",
        "急拡大すると運用事故が増えるため、先に失敗パターンを蓄積・共有した方が、長期的には再現性の高い導入ができる。",
        1, 4, 2,
    ),
    (
        "社内データ整備を最優先し、生成AI導入はデータ品質基準の達成後に実施する",
        "低品質データにAIを接続しても誤った示唆が増えるだけで、投資対効果が低い。マスタ整備と文書体系化が先決である。",
        0, 4, 1,
    ),
    (
        "データ整備は後追いでもよいので、まず生成AI導入で業務の詰まり箇所を特定する",
        "実運用でしか分からないデータ欠損や業務ボトルネックがある。先に使って課題を見つける方が整備の優先順位を決めやすい。",
        2, 4, 2,
    ),
    (
        "生成AI利用ログを全件監査し、プロンプト・出力・参照データの追跡可能性を確保する",
        "監査証跡がなければ説明責任を果たせない。特に規制業界では利用履歴の保存が導入継続の前提条件になる。",
        0, 5, 1,
    ),
    (
        "評価指標を『作業時間削減』だけでなく『意思決定品質』にも拡張して導入効果を測る",
        "短時間化のみを追うと誤判断が増える恐れがある。品質・再作業率・顧客満足まで含めて評価しないと最適化を誤る。",
        1, 5, 2,
    ),
    (
        "生成AI専任組織を設置せず、既存IT部門に内包して全社標準化を優先する",
        "専任組織は俊敏だが分断を生みやすい。既存ITガバナンスの中で進めることで、運用・セキュリティ標準を統一しやすい。",
        0, 3, 1,
    ),
    (
        "あえて生成AI専任のCoEを設置し、部門横断の実装支援と人材育成を集中運営する",
        "既存部門に任せると兼務で推進力が弱くなるため、CoEが横断支援と資産再利用を担った方が導入スピードを上げられる。",
        1, 4, 2,
    ),
    (
        "調達方針として単一ベンダー依存を避け、マルチLLM前提のアーキテクチャを採用する",
        "モデル価格や性能は変動が大きく、ベンダーロックインは経営リスクになる。切替可能な設計で交渉力と継続性を確保する。",
        1, 4, 2,
    ),
    (
        "守りの活用より攻めの新規事業創出を重視し、AI起点のサービス企画を経営KPIに組み込む",
        "コスト削減だけでは差別化が難しいため、生成AIを価値創出の道具として使い、新サービス売上を主要KPIに据えるべきである。",
        2, 4, 2,
    ),
    (
        "業務自動化で余剰化する人員を削減対象にせず、顧客課題探索の職務へ再配置する",
        "短期の人件費削減に偏ると組織学習が止まる。AIで生まれた余力を高付加価値業務に移す方が中長期成長に寄与する。",
        1, 4, 2,
    ),
    (
        "逆に採算改善を優先し、AI自動化による余剰人員は段階的に最適化する",
        "収益悪化局面では固定費の見直しが不可欠であり、再配置だけで吸収できない場合は人員最適化も経営判断として必要になる。",
        2, 3, 2,
    ),
    (
        "プロンプト資産を個人管理させず、社内共有リポジトリでテンプレート化する",
        "個人ノウハウに閉じると再現性が下がる。部門共通テンプレートとして管理することで品質を平準化し、教育コストを下げられる。",
        0, 4, 1,
    ),
    (
        "生成AIの出力をそのまま使うのではなく、根拠リンク提示を必須化して検証可能性を高める",
        "根拠不明な回答は誤りを見抜きにくい。参照元を併記させる運用で、担当者の検証時間を短縮しつつ信頼性を高める。",
        0, 5, 1,
    ),
    (
        "部門ごとに独自導入を認め、現場最適の多様なツール利用を許容する",
        "統一ツールだけでは業務特性に合わない場合がある。現場裁量を残すことで実務適合性が高まり、活用率が向上する。",
        1, 3, 1,
    ),
    (
        "部門独自導入を禁止し、セキュアな社内ポータル経由の利用に一本化する",
        "シャドーAIを放置すると統制不能になる。入口を一本化し、DLPや監査機能を組み込むことでガバナンスを担保する。",
        0, 5, 1,
    ),
    (
        "経営会議資料はまず生成AIでドラフト化し、意思決定の準備時間を半減する",
        "要約・論点整理・比較表作成をAIに任せると、管理職が判断に集中できる。会議の質とスピードの両立が可能になる。",
        0, 4, 1,
    ),
    (
        "生成AI活用を評価制度に反映し、活用成果を昇格・賞与の要件に組み込む",
        "任意利用では浸透が遅いため、評価制度に連動させることで行動変容を促進し、組織全体の学習速度を高める。",
        1, 4, 2,
    ),
    (
        "評価制度への組み込みは避け、まずは心理的安全性を確保して自発的活用を促す",
        "評価連動を急ぐと形式的利用が増える。失敗共有を許容する期間を設けた方が、質の高いユースケースが育ちやすい。",
        1, 4, 2,
    ),
    (
        "対外発信物は生成AI利用の有無を明示し、透明性をブランド価値として打ち出す",
        "AI利用の説明責任を果たすことで顧客の不信感を抑えられる。透明性を競争優位として活用できる可能性がある。",
        2, 4, 1,
    ),
    (
        "高リスク業務では生成AI利用を限定し、従来プロセスを維持して品質事故を防ぐ",
        "医療・法務・安全関連など誤り許容度が低い領域では、人手中心の既存プロセスを維持した方が社会的リスクを抑制できる。",
        0, 5, 1,
    ),
    (
        "生成AIを前提に業務プロセスを再設計し、入力様式や承認フロー自体を抜本的に見直す",
        "既存業務にAIを後付けするだけでは効果が限定的。AIが最大効果を出せるように業務設計そのものを再構築する必要がある。",
        2, 5, 2,
    ),
]

CHALLENGE_DEF = {
    "title": "【企業向け】生成AIを全社活用するにはどのような進め方が有効か",
    "description": (
        "生成AIの活用を検討している企業向けの課題です。"
        "短期の業務効率化だけでなく、ガバナンス、リスク管理、人材育成、新規事業創出まで含めて、"
        "多様な立場から具体的な解決案を募集します。"
    ),
    "templates": GENAI_ENTERPRISE_PROPOSALS,
}


class Command(BaseCommand):
    help = "【企業向け】生成AI活用課題を1件・解決案30件で作成（期限2月27日・結果画面表示用）"

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

        start = timezone.make_aware(datetime(2026, 2, 20, 0, 0, 0))
        total_days = 7
        proposal_deadline, edit_deadline, evaluation_deadline = calculate_phase_deadlines(start, total_days)
        deadline = evaluation_deadline
        reward_amount = Decimal(str(calculate_reward_amount(required_count)))
        adoption_reward = Decimal("500000")

        templates = CHALLENGE_DEF["templates"]

        with transaction.atomic():
            challenge = Challenge.objects.create(
                title=CHALLENGE_DEF["title"],
                description=CHALLENGE_DEF["description"],
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
                conclusion, reasoning = templates[j][0], templates[j][1]
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
                    inn, ins = templates[idx][2], templates[idx][3]
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
                "観点が具体的で、実装時の論点が明確です。",
                "現実的な推進手順が示されていて参考になります。",
                "反対意見も想定されており、議論を深めやすい提案です。",
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

            self.stdout.write(
                self.style.SUCCESS(
                    f"課題 {challenge.id} 作成: {CHALLENGE_DEF['title'][:50]}... ({len(proposals)}件)"
                )
            )

            if not options.get("skip_analysis"):
                try:
                    ChallengeAnalyzer(challenge.id).analyze_challenge()
                    self.stdout.write(self.style.SUCCESS(f"分析完了: 課題 {challenge.id}"))
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"分析エラー: {e}"))

        post_save.connect(analytics_signals.auto_analyze_on_challenge_close, sender=Challenge)
        self.stdout.write(self.style.SUCCESS("完了"))
