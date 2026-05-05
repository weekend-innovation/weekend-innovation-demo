"""
課題分析・まとめ機能のサービス層
"""
import os
import re
import json
import logging
from collections import Counter, defaultdict
from datetime import timedelta
from typing import Dict, List, Any, Tuple, Optional
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.cache import cache

from challenges.models import Challenge
from proposals.models import Proposal, ProposalEditReference
from .models import ChallengeAnalysis, ProposalInsight

User = get_user_model()
logger = logging.getLogger(__name__)


def _get_user_attr_tuple(user) -> Tuple:
    """ユーザーの属性タプル(gender, nationality, age_bucket)を取得（多様性計算用）"""
    try:
        profile = user.proposer_profile
        gender = getattr(profile, 'gender', None) or 'unknown'
        nationality = getattr(profile, 'nationality', None) or 'unknown'
        age_bucket = 'unknown'
        if hasattr(profile, 'birth_date') and profile.birth_date:
            from datetime import date
            today = date.today()
            age = today.year - profile.birth_date.year - (
                (today.month, today.day) < (profile.birth_date.month, profile.birth_date.day)
            )
            age_bucket = (age // 10) * 10 if age >= 0 else 0
        return (gender, nationality, age_bucket)
    except Exception:
        return ('unknown', 'unknown', 'unknown')


def _calculate_diversity_bonus(attr_tuples: List[Tuple]) -> float:
    """
    属性タプルのリストから多様性ボーナスを計算（0〜0.15の範囲）
    全員同じ→0、全員異なる→0.15
    """
    if not attr_tuples:
        return 0.0
    unique = len(set(attr_tuples))
    n = len(attr_tuples)
    if n <= 1:
        return 0.0
    # unique/n が1に近いほど多様。0.15を最大ボーナスとする
    return min(0.15, (unique / n) * 0.15)


class ChallengeAnalyzer:
    """課題分析サービス"""
    
    def __init__(self, challenge_id: int):
        self.challenge_id = challenge_id
        self.challenge = Challenge.objects.get(id=challenge_id)
        self.proposals = Proposal.objects.filter(challenge=challenge_id)
    
    def analyze_challenge(self) -> ChallengeAnalysis:
        """課題の総合分析を実行"""
        
        # 分析レコードを作成または取得
        analysis, created = ChallengeAnalysis.objects.get_or_create(
            challenge=self.challenge,
            defaults={'status': 'processing'}
        )
        
        if not created:
            analysis.status = 'processing'
            analysis.save()
        
        try:
            # 基本統計の計算
            basic_stats = self._calculate_basic_statistics()
            
            # 提案内容の分析
            content_analysis = self._analyze_proposal_content()
            
            # 洞察の生成
            insights = self._generate_insights()
            
            # まとめの生成
            summaries = self._generate_summaries(basic_stats, content_analysis, insights)
            
            # 分析結果を保存
            analysis.total_proposals = basic_stats['total_proposals']
            analysis.unique_proposers = basic_stats['unique_proposers']
            analysis.common_themes = []  # キーワード依存のため廃止
            analysis.innovative_solutions = content_analysis['innovative_solutions']
            analysis.executive_summary = summaries['executive_summary']
            analysis.detailed_analysis = summaries['detailed_analysis']
            analysis.recommendations = summaries['recommendations']
            analysis.recommendations_source = summaries.get('recommendations_source', '')
            
            analysis.mark_as_completed()
            
            # 提案洞察を保存
            self._save_insights(analysis, insights)
            
            return analysis
            
        except Exception as e:
            analysis.mark_as_failed()
            raise e
    
    def _calculate_basic_statistics(self) -> Dict[str, Any]:
        """基本統計を計算"""
        proposals = list(self.proposals)
        
        return {
            'total_proposals': len(proposals),
            'unique_proposers': len(set(p.proposer for p in proposals)),
            'avg_proposal_length': sum(len(p.conclusion + p.reasoning) for p in proposals) / len(proposals) if proposals else 0,
            'submission_timeline': [p.created_at.isoformat() for p in proposals]
        }
    
    def _analyze_proposal_content(self) -> Dict[str, Any]:
        """提案内容を分析（キーワード依存項目は廃止）"""
        proposals = list(self.proposals)
        
        # 革新的解決案の特定（評価＋クラスタ外れ、キーワード不使用）
        innovative_solutions = self._identify_innovative_solutions(proposals)
        
        return {
            'innovative_solutions': innovative_solutions
        }
    
    def _identify_innovative_solutions(self, proposals: List[Proposal]) -> List[Dict[str, Any]]:
        """
        革新的解決案を特定（キーワード不使用）
        - 評価データ: 「この結論を思い付いていましたか？」でNoが多いほど革新性が高い
        - クラスタリングの外れ: 他と似ていない提案を革新的候補とする
        """
        if not proposals:
            return []
        
        # 1. 評価ベースの革新性スコアを計算
        eval_scores = {}
        for proposal in proposals:
            text = proposal.conclusion + ' ' + proposal.reasoning
            eval_scores[proposal.id] = self._calculate_innovation_score(proposal, text)
        
        # 2. クラスタ外れスコアを計算（2件以上の場合）
        outlier_scores = {p.id: 0.5 for p in proposals}  # デフォルトは中立
        if len(proposals) >= 2:
            clustering = ProposalClusteringService()
            result = clustering.cluster_proposals(proposals)
            coords = result.get('coordinates', [])
            if coords:
                import numpy as np
                # proposal_id -> (x, y, cluster)
                coord_map = {c['proposal_id']: (c['x'], c['y'], c['cluster']) for c in coords}
                # クラスタごとの重心を計算
                cluster_points = {}
                for pid, (x, y, cl) in coord_map.items():
                    cluster_points.setdefault(cl, []).append((x, y))
                centroids = {}
                for cl, pts in cluster_points.items():
                    arr = np.array(pts)
                    centroids[cl] = arr.mean(axis=0)
                # 各提案の重心からの距離（クラスタ内での外れ度）
                distances = {}
                for pid, (x, y, cl) in coord_map.items():
                    cent = centroids[cl]
                    dist = np.sqrt((x - cent[0]) ** 2 + (y - cent[1]) ** 2)
                    distances[pid] = dist
                # 0-1に正規化
                if distances:
                    max_d = max(distances.values())
                    if max_d > 0:
                        outlier_scores = {pid: d / max_d for pid, d in distances.items()}
                    else:
                        outlier_scores = {pid: 0.5 for pid in distances}
        
        # 3. 複合スコア（評価60% + クラスタ外れ40%）
        candidates = []
        for proposal in proposals:
            comp = 0.6 * eval_scores[proposal.id] + 0.4 * outlier_scores.get(proposal.id, 0.5)
            candidates.append({
                'proposal_id': proposal.id,
                'innovation_score': round(eval_scores[proposal.id], 4),
                'outlier_score': round(outlier_scores.get(proposal.id, 0.5), 4),
                'composite_score': round(comp, 4),
                'summary': proposal.conclusion[:100] + '...' if len(proposal.conclusion) > 100 else proposal.conclusion
            })
        
        return sorted(candidates, key=lambda x: x['composite_score'], reverse=True)
    
    
    def _generate_insights(self) -> List[Dict[str, Any]]:
        """洞察を生成"""
        insights = []
        proposals = list(self.proposals)
        
        for proposal in proposals:
            text = proposal.conclusion + ' ' + proposal.reasoning
            
            # デバッグログ
            print(f"\n=== 提案ID {proposal.id} の分析 ===")
            print(f"rating: {proposal.rating}, rating_count: {proposal.rating_count}")
            
            # スコア計算（評価・コメント・多様性・参考編集。散布図の位置は使用しない）
            innovation_score = self._calculate_innovation_score(proposal, text)
            insightfulness_score = self._calculate_insightfulness_score(proposal)
            impact_score = self._calculate_impact_score(proposal, text)
            proposal_char_count = len((proposal.conclusion or '') + (proposal.reasoning or ''))
            
            print(f"革新性スコア: {innovation_score}")
            print(f"支持率スコア: {insightfulness_score}")
            print(f"影響度スコア: {impact_score}")
            
            insights.append({
                'proposal_id': proposal.id,
                'innovation_score': innovation_score,
                'insightfulness_score': insightfulness_score,
                'impact_score': impact_score,
                'proposal_char_count': proposal_char_count,
            })
        
        return insights
    
    def _calculate_insightfulness_score(self, proposal) -> float:
        """
        支持率スコアを計算（散布図の位置は使用しない）
        - 示唆性評価（1-5）の平均
        - 評価者属性の多様性ボーナス（多様な視点で支持されているか）
        - コメントを参考に編集したかボーナス
        """
        from proposals.models import ProposalEvaluation
        from django.db.models import Avg
        
        evaluations = ProposalEvaluation.objects.filter(proposal=proposal).select_related('evaluator', 'evaluator__proposer_profile')
        
        if evaluations.count() == 0:
            return 0.5
        
        avg_insight = evaluations.aggregate(Avg('insight_score'))['insight_score__avg']
        if avg_insight is None:
            return 0.5
        
        base = (avg_insight - 1) / 4  # 1→0.0, 5→1.0
        
        # 評価者属性の多様性ボーナス（示唆性を評価した人々の多様性）
        eval_attrs = [_get_user_attr_tuple(e.evaluator) for e in evaluations]
        diversity_bonus = _calculate_diversity_bonus(eval_attrs)
        
        # コメントを参考に編集したかボーナス（支持率に寄与）
        edit_ref_count = ProposalEditReference.objects.filter(proposal=proposal).count()
        edit_bonus = min(0.1, edit_ref_count * 0.05)  # 参考編集1件で0.05、2件で0.1上限
        
        return min(1.0, base + diversity_bonus + edit_bonus)
    
    def _calculate_innovation_score(self, proposal, text: str) -> float:
        """
        革新性スコアを計算
        - 「思い付いていましたか？」の評価（Noが多いほど高）
        - 評価者属性の多様性ボーナス（多様な視点で「思いつかなかった」と評価されているか）
        """
        from proposals.models import ProposalEvaluation
        from django.db.models import Avg
        
        evaluations = ProposalEvaluation.objects.filter(proposal=proposal).select_related('evaluator', 'evaluator__proposer_profile')
        
        if evaluations.count() == 0:
            return 0.5
        
        avg_score = evaluations.aggregate(Avg('score'))['score__avg']
        if avg_score is None:
            return 0.5
        
        base = avg_score / 2  # 0→0.0, 2→1.0
        
        # 評価者属性の多様性ボーナス（革新性を評価した人々の多様性）
        eval_attrs = [_get_user_attr_tuple(e.evaluator) for e in evaluations]
        diversity_bonus = _calculate_diversity_bonus(eval_attrs)
        
        return min(1.0, base + diversity_bonus)
    
    
    def _calculate_impact_score(self, proposal, text: str) -> float:
        """
        影響度スコアを計算
        
        1. コメント数（40%）: 議論の量
        2. ユニークコメンター数（25%）: 参加者の広がり
        3. コメント数の分布（15%）: 少数への偏りなし＝unique/comment_count
        4. コメンター属性の多様性（10%）: 性別・年齢・国籍のばらつき
        5. コメントの推移（10%）: 提案・編集期間内で相対的（微分的）に盛り上がっているか
        """
        import math
        from proposals.models import ProposalComment
        
        comments = list(ProposalComment.objects.filter(
            proposal=proposal, is_deleted=False
        ).select_related('commenter', 'commenter__proposer_profile'))
        comment_count = len(comments)
        
        if comment_count == 0:
            return 0.0
        
        # 1. コメント数スコア（40%）
        comment_score = min(math.log(comment_count + 1) / math.log(31), 1.0) * 0.4
        
        # 2. ユニークコメンター数（25%）
        unique_commenters = len(set(c.commenter_id for c in comments))
        unique_score = min(math.log(unique_commenters + 1) / math.log(16), 1.0) * 0.25
        
        # 3. コメント数の分布（15%）: unique/comment_count、1に近いほど分散
        distribution_ratio = unique_commenters / comment_count
        distribution_score = distribution_ratio * 0.15
        
        # 4. コメンター属性の多様性（10%）
        commenter_attrs = [_get_user_attr_tuple(c.commenter) for c in comments]
        attr_diversity = _calculate_diversity_bonus(commenter_attrs) / 0.15 * 0.1  # 0.15→0.1にスケール
        
        # 5. コメントの推移（ホットな解決案）（10%）: コメント可能期間を前半・後半に分け、
        #    後半にコメントが集中しているほど微分的に盛り上がっている＝高スコア
        challenge = proposal.challenge
        period_end = challenge.edit_deadline or challenge.proposal_deadline or challenge.deadline
        period_start = challenge.created_at
        if period_end and period_start and period_end > period_start:
            mid = period_start + (period_end - period_start) / 2
            second_half = sum(1 for c in comments if c.created_at >= mid)
            second_half_ratio = second_half / comment_count
            # 後半の割合が0.5より大きいほどホット。1.0=全て後半で満点、0.5=均等で0
            hotness = max(0.0, (second_half_ratio - 0.5) * 2)  # 0.5→0, 1.0→1
            hotness_score = hotness * 0.1
        else:
            hotness_score = 0.0
        
        total_impact = comment_score + unique_score + distribution_score + attr_diversity + hotness_score
        
        return min(total_impact, 1.0)
    
    def _generate_summaries(self, basic_stats: Dict, content_analysis: Dict, insights: List[Dict]) -> Dict[str, Any]:
        """まとめ文を生成"""
        
        executive_summary = self._generate_executive_summary(basic_stats, content_analysis)
        detailed_analysis = self._generate_detailed_analysis(content_analysis, insights)
        recommendations, recommendations_source = self._generate_recommendations(content_analysis, insights)
        
        return {
            'executive_summary': executive_summary,
            'detailed_analysis': detailed_analysis,
            'recommendations': recommendations,
            'recommendations_source': recommendations_source
        }
    
    def _generate_executive_summary(self, basic_stats: Dict, content_analysis: Dict) -> str:
        """エグゼクティブサマリーを生成（キーワード非依存）"""
        total_proposals = basic_stats['total_proposals']
        unique_proposers = basic_stats['unique_proposers']
        return f"本課題に対して{unique_proposers}名の提案者から合計{total_proposals}件の解決案が提出されました。"
    
    def _generate_detailed_analysis(self, content_analysis: Dict, insights: List[Dict]) -> str:
        """詳細分析（キーワード依存のため廃止、空を返す）"""
        return ""
    
    def _generate_recommendations(self, content_analysis: Dict, insights: List[Dict]) -> Tuple[str, str]:
        """
        総括を生成：課題と解決案に基づく適切なアドバイス
        LLMが利用可能な場合は精緻な洞察を生成、不可の場合は従来のテンプレートにフォールバック
        
        Returns:
            (総括テキスト, 生成元: 'llm' | 'fallback')
        """
        proposals = list(self.proposals)
        if not proposals:
            return "", ""

        llm_result, skip_reason = self._generate_recommendations_with_llm(insights)
        if llm_result:
            logger.info("課題 %s: Gemini LLMで総括を生成しました", self.challenge.id)
            return llm_result, "llm"
        logger.info(
            "課題 %s: 総括はテンプレートで生成しました（LLM未使用: %s）",
            self.challenge.id,
            skip_reason or "不明"
        )
        return self._generate_recommendations_fallback(proposals, insights), "fallback"

    def _generate_recommendations_with_llm(self, insights: List[Dict]) -> Tuple[Optional[str], Optional[str]]:
        """LLMを使って総括を生成。Gemini API（無料枠）を使用。
        
        Returns:
            (総括テキスト, skip_reason): 成功時は(text, None)、失敗時は(None, 理由)
        """
        from django.conf import settings
        # 無料枠超過でキャッシュされている場合はスキップ
        if cache.get("gemini_quota_exhausted"):
            logger.debug("Gemini API無料枠超過のため、LLM総括をスキップ（1時間後に再試行可能）")
            return None, "無料枠超過（1時間後に再試行可能）"
        api_key = (
            getattr(settings, "GEMINI_API_KEY", None)
            or os.environ.get("GEMINI_API_KEY")
            or os.environ.get("GOOGLE_API_KEY")
        )
        if not api_key:
            logger.debug("GEMINI_API_KEYが未設定のため、LLM総括をスキップ")
            return None, "APIキー未設定"

        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
        except ImportError:
            logger.warning("google-generativeaiパッケージが未インストールのため、LLM総括をスキップ")
            return None, "google-generativeai未インストール"

        proposals = list(self.proposals)
        prop_map = {p.id: p for p in proposals}

        # トップ提案を取得（独創性・支持率・影響度）
        top_orig = max(insights, key=lambda x: (x.get("innovation_score", 0), -x.get("proposal_char_count", 0))) if insights else None
        top_sup = max(insights, key=lambda x: (x.get("insightfulness_score", 0), -x.get("proposal_char_count", 0))) if insights else None
        top_imp = max(insights, key=lambda x: (x.get("impact_score", 0), -x.get("proposal_char_count", 0))) if insights else None

        # クラスタテーマを取得
        cluster_themes = []
        try:
            clustering = ProposalClusteringService()
            result = clustering.cluster_proposals(proposals)
            cluster_info = result.get("cluster_info", [])
            if cluster_info:
                sorted_clusters = sorted(cluster_info, key=lambda c: c.get("size", 0), reverse=True)
                cluster_themes = [c.get("theme", "未分類") for c in sorted_clusters[:5]]
        except Exception as e:
            logger.warning(f"クラスタリング取得エラー（LLM総括用）: {e}")

        def format_proposal(insight: Optional[Dict]) -> str:
            if not insight:
                return "（該当なし）"
            p = prop_map.get(insight.get("proposal_id")) if insight.get("proposal_id") else None
            if not p:
                return "（該当なし）"
            c = (p.conclusion or "")[:200]
            r = (p.reasoning or "")[:300]
            return f"【結論】{c}\n【理由】{r}"

        # プロンプト構築
        system_prompt = """あなたは課題解決のアドバイザーです。企業・自治体が投稿した課題と、提案者から寄せられた解決案を分析し、
採用・実装の判断に役立つ総括を書いてください。散布図や分析サマリーを見れば分かるような表面的な要約ではなく、
課題の本質と解決案の多様な視点を踏まえた、具体的で実践的な洞察・示唆を述べてください。
300字以上600字程度で、箇条書きではなく自然な文章で書いてください。"""

        user_content_parts = [
            f"【課題】",
            f"タイトル: {self.challenge.title}",
            f"内容: {(self.challenge.description or '')[:800]}",
            "",
            f"【解決案の傾向（クラスタ）】{', '.join(cluster_themes) if cluster_themes else '（分類なし）'}",
            "",
            "【代表的な解決案】",
            "■ 最も独創的な解決案（革新性が高い）:",
            format_proposal(top_orig),
            "",
            "■ 最も支持されている解決案（主流の意見に近い）:",
            format_proposal(top_sup),
            "",
            "■ 最も議論が活発な解決案（コメント・関心が集まった）:",
            format_proposal(top_imp),
            "",
            "上記の課題と解決案をもとに、課題投稿者（企業・自治体）向けの総括を作成してください。"
        ]
        user_content = "\n".join(user_content_parts)

        try:
            model_name = getattr(settings, "GEMINI_MODEL", None) or os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
            model = genai.GenerativeModel(
                model_name,
                system_instruction=system_prompt,
                generation_config=genai.GenerationConfig(
                    max_output_tokens=800,
                    temperature=0.7,
                ),
            )
            response = model.generate_content(user_content)
            text = response.text if response and response.text else ""
            if text and len(text.strip()) > 50:
                return text.strip(), None
        except Exception as e:
            err_msg = str(e).lower()
            # 無料枠超過・レート制限（429, ResourceExhausted, quota）の場合はキャッシュしてスキップ
            if (
                "429" in err_msg
                or "resource" in err_msg and "exhausted" in err_msg
                or "quota" in err_msg
                or "rate limit" in err_msg
            ):
                cooldown = getattr(
                    settings, "GEMINI_QUOTA_COOLDOWN_SECONDS", 3600
                )  # デフォルト1時間
                cache.set("gemini_quota_exhausted", True, timeout=cooldown)
                logger.warning(
                    "Gemini API無料枠超過のため、1時間LLM総括をスキップします: %s", e
                )
                return None, "無料枠超過"
            else:
                logger.warning(f"LLM総括生成エラー: {e}")
                return None, f"APIエラー: {type(e).__name__}"

        return None, "応答が空または短すぎる"

    def _generate_recommendations_fallback(self, proposals: List, insights: List[Dict]) -> str:
        """従来のテンプレートで総括を生成（LLM不可時のフォールバック）"""
        parts = []
        try:
            clustering = ProposalClusteringService()
            result = clustering.cluster_proposals(proposals)
            cluster_info = result.get("cluster_info", [])
            if cluster_info:
                sorted_clusters = sorted(cluster_info, key=lambda c: c.get("size", 0), reverse=True)
                themes = [c.get("theme", "未分類") for c in sorted_clusters[:3]]
                if themes:
                    parts.append("解決案の傾向として「" + "」「".join(themes) + "」といった観点が見られます。")
        except Exception:
            pass
        if insights:
            top_orig = max(insights, key=lambda x: (x.get("innovation_score", 0), -x.get("proposal_char_count", 0)))
            top_sup = max(insights, key=lambda x: (x.get("insightfulness_score", 0), -x.get("proposal_char_count", 0)))
            prop_map = {p.id: p for p in proposals}
            for label, insight in [("独創的", top_orig), ("支持", top_sup)]:
                pid = insight.get("proposal_id")
                p = prop_map.get(pid) if pid else None
                if p and p.conclusion:
                    ex = (p.conclusion[:50] + "…") if len(p.conclusion) > 50 else p.conclusion
                    parts.append(f"{label}な視点として「{ex}」が挙げられます。")
        parts.append("これらの解決案を踏まえ、採用・実装時には複数の視点のバランスを検討することを推奨します。")
        return " ".join(parts)
    
    def _save_insights(self, analysis: ChallengeAnalysis, insights: List[Dict]):
        """提案洞察を保存"""
        for insight_data in insights:
            ProposalInsight.objects.update_or_create(
                analysis=analysis,
                proposal_id=insight_data['proposal_id'],
                defaults={
                    'innovation_score': insight_data['innovation_score'],
                    'insightfulness_score': insight_data.get('insightfulness_score', 0.5),
                    'impact_score': insight_data['impact_score'],
                    'proposal_char_count': insight_data.get('proposal_char_count', 0),
                    'key_themes': [],
                    'strengths': [],
                    'concerns': []
                }
            )


def analyze_challenge_on_deadline(challenge_id: int):
    """課題の募集期限の満了時に自動分析を実行"""
    try:
        analyzer = ChallengeAnalyzer(challenge_id)
        return analyzer.analyze_challenge()
    except Exception as e:
        print(f"分析エラー (課題ID: {challenge_id}): {e}")
        return None


class ProposalClusteringService:
    """
    解決案のクラスタリングサービス
    テキスト埋め込みを使用して、似ている解決案をグループ化し、2次元にマッピング
    """
    
    def __init__(self):
        # Sentence Transformerモデルのロード（軽量な日本語モデル）
        # AIモデルを使わずに軽量なクラスタリングを使用
        print("Using lightweight clustering without AI model")
        self.model = None
    
    def cluster_proposals(self, proposals: List[Proposal]) -> Dict[str, Any]:
        """
        解決案をクラスタリングし、2次元座標とクラスタ情報を返す
        
        Returns:
            {
                'coordinates': [{'proposal_id': int, 'x': float, 'y': float, 'cluster': int}, ...],
                'cluster_info': [{'cluster_id': int, 'size': int, 'theme': str}, ...],
                'total_clusters': int
            }
        """
        # 解決案が1件のみの場合は中央に配置
        if len(proposals) < 2:
            return self._default_layout(proposals)
        
        # 軽量なクラスタリングを使用
        return self._lightweight_clustering(proposals)
    
    def _extract_japanese_tokens(self, text: str) -> List[str]:
        """日本語テキストから3文字以上のカタカナ・漢字トークンを抽出"""
        import re
        return re.findall(r'[ァ-ヶー]{3,}|[一-龠々]{3,}', text)

    def _balance_clusters(self, word_vectors, cluster_labels, n_clusters: int):
        """
        最大クラスタが50%超の場合、境界付近の点を他クラスタへ移動してバランスを取る。
        クラスタ数は3のまま維持。
        """
        import numpy as np
        n = len(cluster_labels)
        if n < 4 or n_clusters < 2:
            return cluster_labels
        labels = np.array(cluster_labels, dtype=int)
        max_ratio = 0.5
        max_allowed = max(2, int(n * max_ratio))
        sizes = np.bincount(labels, minlength=n_clusters)
        # タイムアウト回避: 再配分ループに上限を設ける
        max_iterations = max(10, n * 2)
        prev_sizes = None
        for _ in range(max_iterations):
            if sizes.max() <= max_allowed:
                break
            large_cid = int(np.argmax(sizes))
            non_empty = np.where(sizes > 0)[0]
            if len(non_empty) < 2:
                break
            small_cid = int(non_empty[np.argmin(sizes[non_empty])])
            if large_cid == small_cid or sizes[large_cid] <= max_allowed:
                break
            large_mask = labels == large_cid
            large_indices = np.where(large_mask)[0]
            centroids = []
            for cid in range(n_clusters):
                mask = labels == cid
                if mask.sum() > 0:
                    centroids.append(word_vectors[mask].mean(axis=0))
                else:
                    centroids.append(word_vectors.mean(axis=0))
            # 大きいクラスタの点で、小さいクラスタの重心に最も近いものを選ぶ
            dist_to_small = np.linalg.norm(
                word_vectors[large_indices] - centroids[small_cid], axis=1
            )
            n_move = min(sizes[large_cid] - max_allowed, max(1, max_allowed - sizes[small_cid]))
            move_idx = large_indices[np.argsort(dist_to_small)[:n_move]]
            labels[move_idx] = small_cid
            sizes = np.bincount(labels, minlength=n_clusters)
            # 収束しないケース（行き来）を打ち切る
            sizes_tuple = tuple(int(x) for x in sizes.tolist())
            if prev_sizes == sizes_tuple:
                break
            prev_sizes = sizes_tuple
        return labels

    def _lightweight_clustering(self, proposals: List[Proposal]) -> Dict[str, Any]:
        """軽量なクラスタリング（AIモデルを使用しない）"""
        import re
        from collections import defaultdict
        import numpy as np
        
        print("軽量クラスタリング開始")
        
        # テキストを日本語トークンで表現
        texts = []
        for proposal in proposals:
            text = f"{proposal.conclusion} {proposal.reasoning}"
            tokens = self._extract_japanese_tokens(text)
            texts.append(" ".join(tokens))  # TfidfVectorizer用
        
        # TF-IDFベクトル化（共通語の影響を抑え、 discriminative な特徴を強調）
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.cluster import KMeans
        
        def tokenize(s):
            return s.split() if s else []

        vectorizer = TfidfVectorizer(
            tokenizer=tokenize,
            token_pattern=None,
            min_df=1,
            max_df=0.95,  # 95%以上で出現する語は除外（汎用語を抑える）
        )
        try:
            word_vectors = vectorizer.fit_transform(texts).toarray()
        except ValueError:
            from sklearn.feature_extraction.text import CountVectorizer
            vec = CountVectorizer(tokenizer=tokenize, token_pattern=None)
            word_vectors = vec.fit_transform(texts).toarray()
        
        # クラスタ数は2か3に限定（領域を分けてグループ感を明確に）
        n_clusters = min(max(2, len(proposals) // 10), 3)
        
        # K-meansクラスタリング
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(word_vectors)
        # 極端な分布を避ける: 最大クラスタが50%超なら境界付近の点を他クラスタへ移動
        cluster_labels = self._balance_clusters(word_vectors, cluster_labels, n_clusters)
        n_clusters = len(np.unique(cluster_labels))
        print(f"クラスタリング完了: {n_clusters}クラスタ")
        
        # 2次元座標を生成（PCA風の配置）
        from sklearn.decomposition import PCA
        if len(word_vectors) > 1:
            pca = PCA(n_components=2, random_state=42)
            coordinates_2d = pca.fit_transform(word_vectors)
            print(f"PCA前座標範囲: X({coordinates_2d[:, 0].min():.3f}-{coordinates_2d[:, 0].max():.3f}), Y({coordinates_2d[:, 1].min():.3f}-{coordinates_2d[:, 1].max():.3f})")
        else:
            coordinates_2d = np.array([[0.5, 0.5]])
        
        # 座標を0-1の範囲に正規化
        coordinates_2d = self._normalize_coordinates(coordinates_2d)
        print(f"PCA後正規化座標範囲: X({coordinates_2d[:, 0].min():.3f}-{coordinates_2d[:, 0].max():.3f}), Y({coordinates_2d[:, 1].min():.3f}-{coordinates_2d[:, 1].max():.3f})")
        
        # クラスタを円形に配置しつつ散らばりを持たせる（類似点同士は干渉してもよい）
        coordinates_2d = self._adjust_cluster_positions(coordinates_2d, cluster_labels)
        coordinates_2d, innovation_scores, pre_innovation_centroids = self._adjust_positions_by_innovation(
            proposals, coordinates_2d, cluster_labels
        )
        print(f"革新性調整後座標範囲: X({coordinates_2d[:, 0].min():.3f}-{coordinates_2d[:, 0].max():.3f}), Y({coordinates_2d[:, 1].min():.3f}-{coordinates_2d[:, 1].max():.3f})")
        
        # バランスよく中央寄せ：全体の境界を0.1〜0.9にマッピング
        x_min, x_max = coordinates_2d[:, 0].min(), coordinates_2d[:, 0].max()
        y_min, y_max = coordinates_2d[:, 1].min(), coordinates_2d[:, 1].max()
        x_range_raw = x_max - x_min
        y_range_raw = y_max - y_min

        # 1クラスタのみ（全点がほぼ同じ位置に潰れている）の場合は中央に配置
        if x_range_raw < 1e-8 and y_range_raw < 1e-8:
            n = len(coordinates_2d)
            coordinates_2d = np.full((n, 2), 0.5)
            scaled_centroid_map = {int(cid): (0.5, 0.5) for cid in pre_innovation_centroids}
        else:
            x_range = x_range_raw if x_range_raw > 1e-8 else 1.0
            y_range = y_range_raw if y_range_raw > 1e-8 else 1.0
            pad_min, pad_max = 0.1, 0.9
            # ×（独創性の参照点＝オフセット適用前の重心）に同じ変換を適用
            scaled_centroid_map = {}
            for cid, cen in pre_innovation_centroids.items():
                cx, cy = float(cen[0]), float(cen[1])
                sx = pad_min + (cx - x_min) / x_range * (pad_max - pad_min)
                sy = pad_min + (cy - y_min) / y_range * (pad_max - pad_min)
                scaled_centroid_map[int(cid)] = (sx, sy)
            coordinates_2d = self._center_and_pad_coordinates(coordinates_2d)
        print(f"パディング適用後座標範囲: X({coordinates_2d[:, 0].min():.3f}-{coordinates_2d[:, 0].max():.3f}), Y({coordinates_2d[:, 1].min():.3f}-{coordinates_2d[:, 1].max():.3f})")
        
        result = self._format_results(
            proposals, coordinates_2d, cluster_labels, innovation_scores,
            centroid_map_override=scaled_centroid_map
        )
        
        print(f"軽量クラスタリング完了: {result.get('total_clusters', 0)}クラスタ")
        return result
    
    def _generate_embeddings(self, proposals: List[Proposal]):
        """テキスト埋め込みを生成"""
        import numpy as np
        
        # 結論と理由を組み合わせたテキストを作成
        texts = []
        for proposal in proposals:
            text = f"{proposal.conclusion} {proposal.reasoning}"
            texts.append(text)
        
        print(f"Generating embeddings for {len(texts)} proposals...")
        
        # 埋め込み生成
        embeddings = self.model.encode(
            texts, 
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        
        print(f"Embeddings generated: shape={embeddings.shape}")
        return np.array(embeddings)
    
    def _perform_clustering(self, embeddings, n_samples: int):
        """K-meansまたはDBSCANでクラスタリング"""
        from sklearn.cluster import KMeans
        from sklearn.metrics import silhouette_score
        import numpy as np
        
        # サンプル数が2件の場合は2クラスタに分類
        if n_samples == 2:
            kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
            return kmeans.fit_predict(embeddings)
        
        # サンプル数が3件未満の場合は全て同じクラスタ
        if n_samples < 3:
            return np.zeros(n_samples, dtype=int)
        
        # クラスタ数の候補
        max_clusters = min(5, n_samples // 2)  # 最大5クラスタまで
        best_k = 2
        best_score = -1
        
        # シルエットスコアで最適なクラスタ数を選択
        for k in range(2, max_clusters + 1):
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(embeddings)
            
            # 全てのサンプルが同じクラスタに属している場合はスキップ
            if len(np.unique(labels)) > 1:
                score = silhouette_score(embeddings, labels)
                if score > best_score:
                    best_score = score
                    best_k = k
        
        # 最適なクラスタ数でクラスタリング実行
        kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(embeddings)
        
        return cluster_labels
    
    def _reduce_dimensions_with_clusters(self, embeddings, cluster_labels):
        """
        クラスタ情報を考慮した次元削減
        同じクラスタの点を近くに配置
        """
        import numpy as np
        from sklearn.decomposition import PCA
        
        n_samples = len(embeddings)
        
        # サンプル数が少ない場合はPCAのみ使用
        if n_samples < 5:
            reducer = PCA(n_components=2, random_state=42)
            coordinates = reducer.fit_transform(embeddings)
            coordinates = self._normalize_coordinates(coordinates)
            return coordinates
        
        try:
            # t-SNEを使用（クラスタを保持しやすい）
            from sklearn.manifold import TSNE
            
            # perplexityの調整（クラスタサイズを考慮）
            perplexity = min(30, max(5, n_samples // 3))
            
            reducer = TSNE(
                n_components=2,
                random_state=42,
                perplexity=perplexity,
                metric='euclidean',  # クラスタ間の距離を保持
                init='pca',  # PCAで初期化（より安定）
                learning_rate='auto'
            )
            coordinates = reducer.fit_transform(embeddings)
            
        except Exception as e:
            print(f"t-SNE error: {e}, falling back to PCA")
            # エラー時はPCAにフォールバック
            reducer = PCA(n_components=2, random_state=42)
            coordinates = reducer.fit_transform(embeddings)
        
        # 座標を0-1の範囲に正規化
        coordinates = self._normalize_coordinates(coordinates)
        
        # クラスタごとに中心を調整（同じクラスタを更に近づける）
        coordinates = self._adjust_cluster_positions(coordinates, cluster_labels)
        
        return coordinates
    
    def _get_fixed_region_centroids(self, n_clusters: int) -> dict:
        """
        クラスタ数を2または3に限定し、それぞれ専用の固定領域の中心座標を返す。
        領域を分けることでグループの干渉を防ぐ。
        """
        import numpy as np
        # 2クラスタ: 左・右に分離
        # 3クラスタ: 左・中央・右に分離（横並びで明確に区切る）
        if n_clusters == 2:
            centers = [(0.28, 0.5), (0.72, 0.5)]
        else:  # 3
            centers = [(0.22, 0.5), (0.5, 0.5), (0.78, 0.5)]
        return {i: np.array(c) for i, c in enumerate(centers[:n_clusters])}
    
    def _adjust_cluster_positions(self, coordinates, cluster_labels):
        """
        クラスタ間の類似度に基づいて配置。類似度が高いクラスタ同士は近く、
        低いクラスタは遠くに配置する（PCA空間での重心位置の相対関係を維持）。
        """
        import numpy as np

        adjusted = coordinates.copy()
        unique_clusters = np.unique(cluster_labels)

        # 各クラスタの重心を計算（PCA空間での位置＝類似度を反映）
        cluster_centroids = {}
        for cluster_id in unique_clusters:
            cluster_mask = cluster_labels == cluster_id
            cluster_points = coordinates[cluster_mask]
            cluster_centroids[cluster_id] = cluster_points.mean(axis=0)

        n_clusters = len(unique_clusters)
        if n_clusters <= 1:
            return adjusted

        # 重心位置をスタックして範囲を取得
        centroids_arr = np.array([cluster_centroids[cid] for cid in unique_clusters])
        cx_min, cx_max = centroids_arr[:, 0].min(), centroids_arr[:, 0].max()
        cy_min, cy_max = centroids_arr[:, 1].min(), centroids_arr[:, 1].max()
        cx_range = cx_max - cx_min if (cx_max - cx_min) > 1e-8 else 1.0
        cy_range = cy_max - cy_min if (cy_max - cy_min) > 1e-8 else 1.0

        # 0.15〜0.85の範囲にスケール（相対位置を維持＝類似＝近く、非類似＝遠く）
        pad_min, pad_max = 0.15, 0.85
        ideal_centroids = {}
        for i, cluster_id in enumerate(unique_clusters):
            c = cluster_centroids[cluster_id]
            ideal_centroids[cluster_id] = np.array([
                pad_min + (c[0] - cx_min) / cx_range * (pad_max - pad_min),
                pad_min + (c[1] - cy_min) / cy_range * (pad_max - pad_min),
            ])

        # 各クラスタの点をスケール済み重心位置へ移動（クラスタ内の相対位置は維持）
        for cluster_id in unique_clusters:
            cluster_mask = cluster_labels == cluster_id
            cluster_points = adjusted[cluster_mask]

            if len(cluster_points) > 0:
                current_centroid = cluster_points.mean(axis=0)
                ideal_centroid = ideal_centroids[cluster_id]
                move_vector = ideal_centroid - current_centroid

                for i, is_in_cluster in enumerate(cluster_mask):
                    if is_in_cluster:
                        adjusted[i] += move_vector
                        if len(cluster_points) > 1:
                            np.random.seed(42 + int(cluster_id) * 100 + i)
                            noise = np.random.normal(0, 0.02, 2)
                            adjusted[i] += noise

        adjusted = np.clip(adjusted, 0, 1)
        return adjusted
    
    def _get_innovation_scores(self, proposals: List[Proposal]) -> List[float]:
        """
        各提案の独創性スコアを計算（評価「思い付いていましたか」＋評価者多様性）
        0-2の評価スコア（No多い＝独創的＝高スコア）を0-1に正規化
        """
        from proposals.models import ProposalEvaluation
        scores = []
        for proposal in proposals:
            evaluations = list(
                ProposalEvaluation.objects.filter(proposal=proposal)
                .select_related('evaluator', 'evaluator__proposer_profile')
            )
            if not evaluations:
                scores.append(0.5)
            else:
                avg_score = sum(e.score for e in evaluations) / len(evaluations)
                base = avg_score / 2.0  # 0-2 → 0-1（No が多い＝独創的＝1.0）
                eval_attrs = [_get_user_attr_tuple(e.evaluator) for e in evaluations]
                diversity_bonus = _calculate_diversity_bonus(eval_attrs)
                scores.append(min(1.0, base + diversity_bonus))
        return scores
    
    def _adjust_positions_by_innovation(self, proposals, coordinates, cluster_labels, region_centroids=None):
        """
        独創性スコアに基づいて、各点をクラスタ重心（×）から外側へオフセット。
        region_centroids 指定時は固定領域内に収め、グループの干渉を防ぐ。
        """
        import numpy as np
        
        adjusted = coordinates.copy()
        unique_clusters = np.unique(cluster_labels)
        
        # 重心：固定領域があればそれを使用、なければPCAの重心
        if region_centroids:
            cluster_centroids = {int(cid): np.array(region_centroids[cid]) for cid in unique_clusters}
        else:
            cluster_centroids = {}
            for cluster_id in unique_clusters:
                cluster_mask = cluster_labels == cluster_id
                cluster_points = coordinates[cluster_mask]
                cluster_centroids[cluster_id] = cluster_points.mean(axis=0)
        
        # 各提案の独創性スコアを計算（評価＋多様性）
        innovation_scores = np.array(self._get_innovation_scores(proposals))
        print(f"独創性スコア範囲: {innovation_scores.min():.3f}-{innovation_scores.max():.3f}")
        
        # 相対独創性に比例して配置。最低の点も×に重ねない（配慮のため）
        n_proposals = len(adjusted)
        min_by_cluster = {}
        max_rel_by_cluster = {}
        for cid in unique_clusters:
            mask = cluster_labels == cid
            scores = innovation_scores[mask]
            min_by_cluster[cid] = float(scores.min())
            rng = float(scores.max() - scores.min())
            max_rel_by_cluster[cid] = rng if rng > 1e-8 else 1.0
        
        min_offset = 0.03  # 最低の点も×から離す（「独創性ゼロ」に見えないよう）
        if region_centroids:
            max_radius = 0.12
            n_scale = (40.0 / max(40, n_proposals)) ** 0.5
            base_weight = max_radius
        else:
            base_weight = 0.38  # 独創性による散らばりを抑える
            n_scale = (40.0 / max(40, n_proposals)) ** 0.5
        innovation_weight = base_weight * n_scale
        
        # PCAのクラスタ重心（方向の基準用）
        pca_centroids = {}
        for cid in unique_clusters:
            mask = cluster_labels == cid
            pca_centroids[cid] = coordinates[mask].mean(axis=0)
        
        global_center = np.array([0.5, 0.5])
        for i in range(len(adjusted)):
            cluster_id = cluster_labels[i]
            centroid = cluster_centroids[cluster_id]
            min_inn = min_by_cluster[cluster_id]
            max_rel = max_rel_by_cluster[cluster_id]
            rel_score = innovation_scores[i] - min_inn
            rel_norm = rel_score / max_rel if max_rel > 1e-8 else 0.0
            
            # 方向: PCA上でクラスタ重心からのベクトル（類似性の相対位置を維持）
            vec = coordinates[i] - pca_centroids[cluster_id]
            dist = np.linalg.norm(vec)
            if dist > 1e-8:
                direction = vec / dist
            else:
                direction = coordinates[i] - global_center
                dn = np.linalg.norm(direction)
                direction = (direction / dn) if dn > 1e-8 else np.array([1.0, 0.0])
            
            # rel_norm=0 でも min_offset で×から離す
            total_dist = min_offset + innovation_weight * rel_norm
            adjusted[i] = centroid + total_dist * direction
        
        adjusted = np.clip(adjusted, 0, 1)
        # ×の参照点として使用した重心（オフセット適用前）を返す
        return adjusted, innovation_scores, cluster_centroids
    
    def _calculate_impact_score(self, proposal) -> float:
        """
        影響度スコアを計算（ChallengeAnalyzer と同一ロジック）
        コメント数・ユニーク数・分布・多様性・ホットさの複合指標
        """
        import math
        from proposals.models import ProposalComment
        
        comments = list(ProposalComment.objects.filter(
            proposal=proposal, is_deleted=False
        ).select_related('commenter', 'commenter__proposer_profile'))
        comment_count = len(comments)
        if comment_count == 0:
            return 0.0
        
        comment_score = min(math.log(comment_count + 1) / math.log(31), 1.0) * 0.4
        unique_commenters = len(set(c.commenter_id for c in comments))
        unique_score = min(math.log(unique_commenters + 1) / math.log(16), 1.0) * 0.25
        distribution_ratio = unique_commenters / comment_count
        distribution_score = distribution_ratio * 0.15
        commenter_attrs = [_get_user_attr_tuple(c.commenter) for c in comments]
        attr_diversity = _calculate_diversity_bonus(commenter_attrs) / 0.15 * 0.1
        
        challenge = proposal.challenge
        period_end = challenge.edit_deadline or challenge.proposal_deadline or challenge.deadline
        period_start = challenge.created_at
        if period_end and period_start and period_end > period_start:
            mid = period_start + (period_end - period_start) / 2
            second_half = sum(1 for c in comments if c.created_at >= mid)
            second_half_ratio = second_half / comment_count
            hotness = max(0.0, (second_half_ratio - 0.5) * 2)
            hotness_score = hotness * 0.1
        else:
            hotness_score = 0.0
        
        return min(
            comment_score + unique_score + distribution_score + attr_diversity + hotness_score,
            1.0
        )
    
    def _center_and_pad_coordinates(self, coordinates):
        """
        座標を0.1〜0.9の範囲に再スケールし、端に寄りすぎないようバランスを取る
        """
        import numpy as np
        x_min, x_max = coordinates[:, 0].min(), coordinates[:, 0].max()
        y_min, y_max = coordinates[:, 1].min(), coordinates[:, 1].max()
        x_range = x_max - x_min
        y_range = y_max - y_min
        if x_range < 1e-8:
            x_range = 1.0
        if y_range < 1e-8:
            y_range = 1.0
        # 0.1〜0.9の範囲にマッピング（10%マージン）
        pad_min, pad_max = 0.1, 0.9
        x_scaled = pad_min + (coordinates[:, 0] - x_min) / x_range * (pad_max - pad_min)
        y_scaled = pad_min + (coordinates[:, 1] - y_min) / y_range * (pad_max - pad_min)
        return np.column_stack([x_scaled, y_scaled])
    
    def _normalize_coordinates(self, coordinates):
        """座標を0-1の範囲に正規化"""
        import numpy as np
        
        min_vals = coordinates.min(axis=0)
        max_vals = coordinates.max(axis=0)
        
        # ゼロ除算を避ける
        ranges = max_vals - min_vals
        ranges[ranges == 0] = 1
        
        normalized = (coordinates - min_vals) / ranges
        return normalized
    
    def _format_results(self, proposals: List[Proposal], coordinates_2d, cluster_labels, innovation_scores=None, centroid_map_override=None) -> Dict[str, Any]:
        """結果を整形"""
        from collections import Counter
        from proposals.models import ProposalComment
        from selections.models import Selection
        
        # 選出されたユーザーのリストを取得
        challenge = proposals[0].challenge if proposals else None
        selected_user_ids = set()
        if challenge:
            try:
                selection = Selection.objects.filter(challenge=challenge, status='completed').first()
                if selection:
                    selected_user_ids = set(selection.selected_users.values_list('id', flat=True))
            except Exception as e:
                print(f"選出ユーザー取得エラー: {e}")
        
        # 座標とクラスタ情報を結合
        coordinates_data = []
        for i, proposal in enumerate(proposals):
            # 提案者名を安全に取得
            try:
                proposer_name = proposal.proposer.username if proposal.proposer else '不明'
            except:
                proposer_name = '不明'
            
            # 匿名名を取得
            anonymous_name = '不明'
            try:
                from selections.models import ChallengeUserAnonymousName
                ch = proposal.challenge if proposal else None
                anon_name_obj = ChallengeUserAnonymousName.objects.filter(
                    challenge=ch,
                    user=proposal.proposer
                ).select_related('anonymous_name').first()
                if anon_name_obj and anon_name_obj.anonymous_name:
                    anonymous_name = anon_name_obj.anonymous_name.name
            except Exception as e:
                print(f"匿名名取得エラー: {e}")
            
            # コメント数を取得
            comment_count = ProposalComment.objects.filter(
                proposal=proposal,
                is_deleted=False
            ).count()
            
            # 影響度スコアを計算（コメント数・ユニーク数・多様性等の複合指標）
            impact_score = self._calculate_impact_score(proposal)
            
            # 基本データ（innovation_scoreは散布図の×からの距離と同一基準）
            innovation_score = float(innovation_scores[i]) if innovation_scores is not None and i < len(innovation_scores) else None
            coordinate_item = {
                'proposal_id': proposal.id,
                'x': float(coordinates_2d[i][0]),
                'y': float(coordinates_2d[i][1]),
                'cluster': int(cluster_labels[i]),
                'conclusion': proposal.conclusion,
                'proposer_name': proposer_name,
                'anonymous_name': anonymous_name,
                'comment_count': comment_count,
                'impact_score': round(impact_score, 4),
                'innovation_score': round(innovation_score, 4) if innovation_score is not None else None,
            }
            
            # 選出されたユーザーの場合は属性情報を追加
            if proposal.proposer and proposal.proposer.id in selected_user_ids:
                coordinate_item['is_selected'] = True
                # ProposerProfileから属性情報を取得
                try:
                    profile = proposal.proposer.proposer_profile
                    coordinate_item['nationality'] = profile.nationality if hasattr(profile, 'nationality') else None
                    coordinate_item['gender'] = profile.gender if hasattr(profile, 'gender') else None
                    # 年齢を生年月日から計算
                    if hasattr(profile, 'birth_date') and profile.birth_date:
                        from datetime import date
                        today = date.today()
                        age = today.year - profile.birth_date.year - ((today.month, today.day) < (profile.birth_date.month, profile.birth_date.day))
                        coordinate_item['age'] = age
                    else:
                        coordinate_item['age'] = None
                except Exception as e:
                    print(f"プロフィール取得エラー (User ID: {proposal.proposer.id}): {e}")
                    coordinate_item['nationality'] = None
                    coordinate_item['gender'] = None
                    coordinate_item['age'] = None
            else:
                coordinate_item['is_selected'] = False
            
            coordinates_data.append(coordinate_item)
        
        # 課題全体で頻出する語（トピック語）を抽出→クラスタ差別化のため除外
        topic_words = self._get_topic_words(proposals)

        # クラスタ情報を集計
        cluster_counter = Counter(cluster_labels)
        cluster_info = []
        for cluster_id, size in cluster_counter.items():
            cluster_proposals = [p for p, label in zip(proposals, cluster_labels) if label == cluster_id]
            theme, main_points_summary = self._extract_cluster_theme_and_summary(
                cluster_proposals, topic_words
            )
            cluster_info.append({
                'cluster_id': int(cluster_id),
                'size': size,
                'theme': theme,
                'main_points_summary': main_points_summary
            })

        # 結果画面の価値向上：要約・判定・クラスタ比較を付与
        cluster_info, balance_summary, majority_minority_summary, cluster_comparison = self._build_result_summaries(
            proposals, coordinates_2d, cluster_labels, innovation_scores, cluster_info
        )
        
        # 軸の意味を自動生成
        axis_labels = self._generate_axis_labels(proposals, coordinates_2d, cluster_labels)
        
        # クラスタ重心（×）：オフセット適用前の重心を使用し、独創性スコアとの整合を保つ
        import numpy as np
        unique_clusters = np.unique(cluster_labels)
        cluster_centroids = []
        if centroid_map_override:
            centroid_map = centroid_map_override
            for cluster_id in unique_clusters:
                cx, cy = centroid_map.get(int(cluster_id), (0.5, 0.5))
                cluster_centroids.append({'cluster_id': int(cluster_id), 'x': float(cx), 'y': float(cy)})
        else:
            centroid_map = {}
            for cluster_id in unique_clusters:
                mask = cluster_labels == cluster_id
                pts = coordinates_2d[mask]
                cx, cy = float(pts[:, 0].mean()), float(pts[:, 1].mean())
                cluster_centroids.append({'cluster_id': int(cluster_id), 'x': cx, 'y': cy})
                centroid_map[int(cluster_id)] = (cx, cy)
        
        # 「最も独創的な解決案」：独創性スコアが最大の解決案を選ぶ
        # 散布図の×からの距離も同じ独創性スコアで決まるため、視覚と一致する
        most_original_proposal_id = None
        most_original_innovation_score = None
        if innovation_scores is not None and len(innovation_scores) > 0 and len(proposals) > 0:
            best_i = int(np.argmax(innovation_scores))
            most_original_proposal_id = proposals[best_i].id
            most_original_innovation_score = float(innovation_scores[best_i])
        
        result = {
            'coordinates': coordinates_data,
            'cluster_info': cluster_info,
            'cluster_centroids': cluster_centroids,
            'total_clusters': len(cluster_counter),
            'axis_labels': axis_labels,
            'balance_summary': balance_summary,
            'majority_minority_summary': majority_minority_summary,
            'cluster_comparison': cluster_comparison,
        }
        if most_original_proposal_id is not None:
            result['most_original_proposal_id'] = most_original_proposal_id
            if most_original_innovation_score is not None:
                result['most_original_innovation_score'] = round(most_original_innovation_score, 4)
        return result

    def _build_result_summaries(
        self, proposals: List[Proposal], coordinates_2d, cluster_labels,
        innovation_scores, cluster_info: List[Dict]
    ) -> tuple:
        """
        結果画面用：合意/独創の要約、クラスタ判定（採用向き/慎重検討）、
        傾向・強み・懸念、多数派vs少数派、クラスタ間の似ている点・違う点を付与
        """
        import numpy as np

        n_proposals = len(proposals)
        n_clusters = len(cluster_info)
        if n_clusters == 0:
            return cluster_info, "", "", {"similar_points": [], "different_points": []}

        # --- バランス要約（合意が高い案 vs 独創的な案）---
        if innovation_scores is not None and len(innovation_scores) == n_proposals:
            inv = np.array(innovation_scores, dtype=float)
            near_consensus = int(np.sum(inv < 0.4))   # ×に近い＝合意寄り
            unique_side = int(np.sum(inv > 0.6))     # 独創寄り
            mid = n_proposals - near_consensus - unique_side
            if near_consensus > 0 and unique_side > 0:
                balance_summary = (
                    f"合意に近い解決案が{near_consensus}件、独創的な解決案が{unique_side}件あり、"
                    "バランスの取れた意見分布です。"
                )
            elif near_consensus >= n_proposals // 2:
                balance_summary = (
                    f"合意に近い解決案が多く（{near_consensus}件）。"
                    "方針がまとまりつつある一方、多様な視点の追加検討も有効です。"
                )
            elif unique_side >= n_proposals // 2:
                balance_summary = (
                    f"独創的な解決案が多く（{unique_side}件）。"
                    "多様なアイデアが集まっているため、採用時は合意度も併せて確認することをおすすめします。"
                )
            else:
                balance_summary = (
                    f"合意寄り{near_consensus}件、中間{mid}件、独創寄り{unique_side}件です。"
                    "全体の傾向を踏まえ、採用候補のバランスを検討してください。"
                )
        else:
            balance_summary = "解決案の分布を踏まえ、合意度と独創性のバランスを確認してください。"

        # --- クラスタごとに判定・強み・懸念を付与 ---
        sizes = [c["size"] for c in cluster_info]
        max_size = max(sizes) if sizes else 0
        total = sum(sizes)
        avg_size = total / n_clusters if n_clusters else 0

        extended_cluster_info = []
        for c in cluster_info:
            size = c["size"]
            theme = c.get("theme", "")
            main_points = c.get("main_points_summary", "")

            # 判定：採用向き / 慎重検討
            if size >= avg_size * 0.8 and size >= 2:
                judgment = "採用に向いている"
            elif size <= 1 or (n_clusters > 1 and size < total * 0.15):
                judgment = "慎重検討が必要（少数意見）"
            else:
                judgment = "慎重検討が必要（内容の確認を推奨）"

            # 強み：主要論点があればそれ、なければ傾向から
            strength = main_points if main_points else f"「{theme}」に議論が集約されています。"

            # 懸念
            if size <= 1:
                concern = "件数が少ないため、採用時は理由の記録を残すことを推奨します。"
            elif n_clusters > 1 and size < total * 0.2:
                concern = "少数派の意見のため、他クラスタとの整合性を確認してください。"
            else:
                concern = "特になし"

            # 懸念を防ぐために参考になる解決案（他クラスタから1〜2件）
            recommended_proposal_ids = []
            if concern != "特になし" and n_clusters >= 2:
                other_clusters = [oc for oc in cluster_info if oc["cluster_id"] != c["cluster_id"]]
                if other_clusters:
                    # 最大サイズの他クラスタから参考案を選ぶ（整合性・バランスのため）
                    other_by_size = sorted(other_clusters, key=lambda x: x["size"], reverse=True)
                    for oc in other_by_size[:2]:  # 最大2クラスタまで
                        indices_in_oc = [i for i, lab in enumerate(cluster_labels) if lab == oc["cluster_id"]]
                        for idx in indices_in_oc[:2]:  # 各クラスタから最大2件
                            if idx < len(proposals):
                                recommended_proposal_ids.append(proposals[idx].id)
                        if len(recommended_proposal_ids) >= 2:
                            break
                    recommended_proposal_ids = recommended_proposal_ids[:2]

            extended_cluster_info.append({
                **c,
                "judgment": judgment,
                "strength": strength,
                "concern": concern,
                "recommended_proposal_ids": recommended_proposal_ids,
            })
        cluster_info = extended_cluster_info

        # --- 多数派 vs 少数派 ---
        sorted_by_size = sorted(cluster_info, key=lambda x: x["size"], reverse=True)
        if len(sorted_by_size) >= 2:
            maj = sorted_by_size[0]
            min_c = sorted_by_size[-1]
            majority_minority_summary = (
                f"多数派の意見（{maj['size']}件）：{maj['theme']}。"
                f"少数派の意見（{min_c['size']}件）：{min_c['theme']}。"
            )
        elif len(sorted_by_size) == 1:
            majority_minority_summary = f"全件が同一の傾向（{sorted_by_size[0]['theme']}）です。"
        else:
            majority_minority_summary = ""

        # --- クラスタ間の似ている点・違う点 ---
        themes = [c.get("theme", "") for c in cluster_info]
        if n_clusters >= 2:
            # 簡易：キーワード（・区切り）の共通部分と差分
            words_per = [set(t.replace("・", " ").split()) for t in themes if t]
            common = set.intersection(*words_per) if words_per else set()
            all_words = set()
            for s in words_per:
                all_words |= s
            different = all_words - common
            similar_points = list(common)[:5] if common else []
            different_points = list(different)[:5] if different else []
            cluster_comparison = {
                "similar_points": similar_points,
                "different_points": different_points,
            }
        else:
            cluster_comparison = {"similar_points": [], "different_points": []}

        return cluster_info, balance_summary, majority_minority_summary, cluster_comparison
    
    def _generate_axis_labels(self, proposals: List[Proposal], coordinates_2d, cluster_labels) -> Dict[str, Any]:
        """
        座標軸の意味を自動生成
        X軸とY軸が何を表すかをAIが推測
        """
        import numpy as np
        import re
        from collections import Counter
        
        # X軸の両端（左端と右端）の解決案を抽出
        x_coords = coordinates_2d[:, 0]
        left_idx = np.argmin(x_coords)
        right_idx = np.argmax(x_coords)
        
        # Y軸の両端（下端と上端）の解決案を抽出
        y_coords = coordinates_2d[:, 1]
        bottom_idx = np.argmin(y_coords)
        top_idx = np.argmax(y_coords)
        
        # X軸の意味を推定
        x_axis = self._infer_axis_meaning(
            [proposals[left_idx]],
            [proposals[right_idx]],
            'x'
        )
        
        # Y軸の意味を推定
        y_axis = self._infer_axis_meaning(
            [proposals[bottom_idx]],
            [proposals[top_idx]],
            'y'
        )
        
        return {
            'x_axis': x_axis,
            'y_axis': y_axis
        }
    
    def _infer_axis_meaning(self, left_proposals: List[Proposal], right_proposals: List[Proposal], axis: str) -> Dict[str, str]:
        """
        軸のラベルを返す（キーワード非依存のため汎用ラベルのみ）
        """
        if axis == 'x':
            return {'left': 'タイプA', 'right': 'タイプB'}
        return {'left': 'タイプC', 'right': 'タイプD'}
    
    def _merge_clusters_by_theme(self, proposals: List[Proposal], cluster_labels: Any) -> Any:
        """
        同じテーマの「小規模クラスタ」（各2件以下）のみマージする。
        大規模クラスタの統合は行わず、極端な28:1:1分布を防ぐ。
        """
        import numpy as np
        from collections import defaultdict
        unique_labels = np.unique(cluster_labels)
        theme_to_clusters = defaultdict(list)
        for cid in unique_labels:
            mask = cluster_labels == cid
            size = int(sum(mask))
            cluster_proposals = [p for p, m in zip(proposals, mask) if m]
            theme = self._extract_cluster_theme(cluster_proposals)
            theme_to_clusters[theme].append((cid, size))
        old_to_new = {}
        new_id = 0
        for theme, cluster_list in theme_to_clusters.items():
            small_only = [(cid, sz) for cid, sz in cluster_list if sz <= 2]
            if len(small_only) >= 2:
                for cid, _ in small_only:
                    old_to_new[cid] = new_id
                new_id += 1
                for cid, sz in cluster_list:
                    if sz > 2:
                        old_to_new[cid] = new_id
                        new_id += 1
            else:
                for cid, _ in cluster_list:
                    old_to_new[cid] = new_id
                    new_id += 1
        return np.array([old_to_new[int(x)] for x in cluster_labels])

    def _get_topic_words(self, proposals: List[Proposal]) -> set:
        """
        課題全体で高頻出する語（トピック語）を抽出。
        これらはクラスタ間の差別化に使わない（例：「生成AI」課題では「生成」が全クラスタに出るため除外）
        """
        from collections import Counter
        import re

        STOP_WORDS = {
            'する', 'ある', 'いる', 'こと', 'もの', 'ため', 'よう', 'その', 'この', 'それ',
            'これ', 'できる', 'られる', 'という', 'について', 'による', 'ための', 'など',
        }

        # 各提案に含まれる語の集合
        doc_words = []
        for p in proposals:
            text = f"{p.conclusion} {p.reasoning}"
            words = set(re.findall(r'[ァ-ヶー]{3,}|[一-龠々]{2,}', text))
            words -= STOP_WORDS
            doc_words.append(words)

        n_docs = len(doc_words)
        if n_docs < 2:
            return set()

        # 語の出現ドキュメント数を集計
        df = Counter()
        for words in doc_words:
            for w in words:
                if len(w) >= 2:
                    df[w] += 1

        # 全提案の50%超に出現する語をトピック語とする（課題の共通テーマ）
        threshold = max(2, n_docs * 0.5)
        return {w for w, c in df.items() if c >= threshold}

    def _extract_cluster_theme(self, proposals: List[Proposal]) -> str:
        """クラスタ内の解決案から共通テーマを抽出（後方互換用・マージ用）"""
        theme, _ = self._extract_cluster_theme_and_summary(proposals, set())
        return theme

    def _extract_cluster_theme_and_summary(
        self, proposals: List[Proposal], topic_words: set
    ) -> tuple:
        """
        クラスタ内の解決案からテーマと主要論点の要約を抽出
        - theme（類似意見の傾向）: このクラスタを他と区別する上位2-3キーワード（トピック語除外後）
        - main_points_summary（このクラスタの主要な論点）: 何が論じられているかの説明文
        二つを差別化：themeは短いラベル、main_pointsは具体的な内容の要約文
        """
        from collections import Counter
        import re

        STOP_WORDS = {
            'する', 'ある', 'いる', 'こと', 'もの', 'ため', 'よう', 'その', 'この', 'それ',
            'これ', 'できる', 'られる', 'という', 'について', 'による', 'ための', 'など',
        }

        all_words = []
        for proposal in proposals:
            text = f"{proposal.conclusion} {proposal.reasoning}"
            words = re.findall(r'[ァ-ヶー]{3,}|[一-龠々]{2,}', text)
            all_words.extend(words)

        if not all_words:
            return f"クラスタ（{len(proposals)}件）", ""

        word_counter = Counter(all_words)
        # ストップワード・トピック語を除外してクラスタ固有の語を取得
        exclude = STOP_WORDS | topic_words
        filtered = [(w, c) for w, c in word_counter.most_common(15)
                    if w not in exclude and len(w) >= 2]

        distinct_keywords = [w for w, _ in filtered[:8]]
        theme = '・'.join(distinct_keywords[:3]) if distinct_keywords else f"クラスタ（{len(proposals)}件）"

        # 主要論点：類似意見の傾向と同じキーワードを繰り返さず、議論の「観点・種類」を別形式で表現
        main_points_summary = self._build_main_points_summary(distinct_keywords[:5])

        return theme, main_points_summary

    def _build_main_points_summary(self, keywords: list) -> str:
        """
        「主要な論点」用の要約文を生成。
        類似意見の傾向（キーワードラベル）と重複せず、議論の観点・性質を簡潔に説明する。
        """
        if not keywords:
            return ""
        kw_set = set(w for w in keywords if len(w) >= 2)
        if not kw_set:
            return ""

        # 議論の観点を表すカテゴリ。具体的な観点を先にし、汎用な観点を後に（グループ差別化のため）
        CATEGORIES = [
            ({'作業者', '人材', 'スキル', '教育'}, "人材・スキル向上の観点"),
            ({'データ', '学習', '分析'}, "データ駆動・学習技術の活用"),
            ({'最適化', '提案', '戦略', '施策'}, "最適化・戦略レベルの提案"),
            ({'品質', '管理', '検証'}, "品質管理・検証の観点"),
            ({'サプライチェーン', '物流', '供給'}, "サプライチェーン・物流"),
            ({'現場', '製造現場', '活用', '導入', '実装', '応用'}, "現場での具体的な応用・導入"),
            ({'設計', '工程', '生産', 'プロセス'}, "設計・工程の効率化・革新"),
        ]
        matched = []
        for cats, label in CATEGORIES:
            if kw_set & cats:
                matched.append(label)
        if matched:
            # トピックは最大2つに制限（3グループで6トピック程度に分散し分かりやすくする）
            return "、".join(matched[:2]) + "に焦点を当てた議論が中心です。"

        # マッチしない場合は、4番目以降のキーワードで補足（themeと重複しにくい）
        extra = [w for w in keywords[3:6] if w in kw_set and len(w) >= 2]
        if len(extra) == 1:
            return f"{extra[0]}などの観点も含まれています。"
        if len(extra) >= 2:
            return "、".join(extra[:2]) + "などの観点も含まれています。"
        return ""
    
    def _default_layout(self, proposals: List[Proposal]) -> Dict[str, Any]:
        """モデルが利用できない場合のデフォルトレイアウト"""
        import numpy as np
        
        # 円形にランダム配置
        coordinates_data = []
        for i, proposal in enumerate(proposals):
            angle = 2 * np.pi * i / len(proposals)
            x = 0.5 + 0.3 * np.cos(angle)
            y = 0.5 + 0.3 * np.sin(angle)
            
            # 提案者名を安全に取得
            try:
                proposer_name = proposal.proposer.username if proposal.proposer else '不明'
            except:
                proposer_name = '不明'
            
            # 匿名名を取得
            anonymous_name = '不明'
            try:
                from selections.models import ChallengeUserAnonymousName
                ch = proposal.challenge if proposal else None
                anon_name_obj = ChallengeUserAnonymousName.objects.filter(
                    challenge=ch, user=proposal.proposer
                ).select_related('anonymous_name').first()
                if anon_name_obj and anon_name_obj.anonymous_name:
                    anonymous_name = anon_name_obj.anonymous_name.name
            except Exception:
                pass
            # コメント数・影響度を取得
            from proposals.models import ProposalComment
            comment_count = ProposalComment.objects.filter(
                proposal=proposal,
                is_deleted=False
            ).count()
            impact_score = self._calculate_impact_score(proposal)
            
            coordinates_data.append({
                'proposal_id': proposal.id,
                'x': float(x),
                'y': float(y),
                'cluster': 0,
                'conclusion': proposal.conclusion,
                'proposer_name': proposer_name,
                'anonymous_name': anonymous_name,
                'comment_count': comment_count,
                'impact_score': round(impact_score, 4)
            })
        
        n = len(proposals)
        single_cluster = {
            'cluster_id': 0, 'size': n, 'theme': '全解決案', 'main_points_summary': '',
            'judgment': '採用に向いている' if n >= 2 else '慎重検討が必要（件数が少ないため）',
            'strength': '全解決案が一つの傾向にまとまっています。' if n >= 2 else '内容を確認のうえ検討してください。',
            'concern': '特になし' if n >= 2 else '件数が少ないため、理由の記録を残すことを推奨します。',
        }
        result = {
            'coordinates': coordinates_data,
            'cluster_info': [single_cluster],
            'cluster_centroids': [{'cluster_id': 0, 'x': 0.5, 'y': 0.5}],
            'total_clusters': 1,
            'axis_labels': {
                'x_axis': {'left': 'タイプA', 'right': 'タイプB'},
                'y_axis': {'left': 'タイプC', 'right': 'タイプD'}
            },
            'balance_summary': '全件が同一傾向のため、合意と独創の分布はありません。' if n <= 1 else '1グループのため、合意と独創のバランスはクラスタ内のばらつきで確認してください。',
            'majority_minority_summary': '',
            'cluster_comparison': {'similar_points': [], 'different_points': []},
        }
        if proposals:
            scores = self._get_innovation_scores(proposals)
            best_i = scores.index(max(scores))
            result['most_original_proposal_id'] = proposals[best_i].id
            result['most_original_innovation_score'] = round(scores[best_i], 4)
        return result