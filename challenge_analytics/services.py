"""
課題分析・まとめ機能のサービス層
"""
import re
import json
from collections import Counter, defaultdict
from typing import Dict, List, Any, Tuple
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

from challenges.models import Challenge
from proposals.models import Proposal
from .models import ChallengeAnalysis, ProposalInsight

User = get_user_model()


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
            analysis.common_themes = content_analysis['common_themes']
            analysis.innovative_solutions = content_analysis['innovative_solutions']
            analysis.executive_summary = summaries['executive_summary']
            analysis.detailed_analysis = summaries['detailed_analysis']
            analysis.recommendations = summaries['recommendations']
            
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
        """提案内容を分析"""
        proposals = list(self.proposals)
        
        # 共通テーマの抽出
        common_themes = self._extract_common_themes(proposals)
        
        # 革新的解決案の特定
        innovative_solutions = self._identify_innovative_solutions(proposals)
        
        return {
            'common_themes': common_themes,
            'innovative_solutions': innovative_solutions
        }
    
    def _extract_common_themes(self, proposals: List[Proposal]) -> List[Dict[str, Any]]:
        """共通テーマを抽出"""
        # キーワードの頻度分析
        all_text = ' '.join([p.conclusion + ' ' + p.reasoning for p in proposals])
        
        # 日本語のキーワードパターン
        keywords = self._extract_japanese_keywords(all_text)
        
        # 頻度順にソート
        theme_counts = Counter(keywords)
        common_themes = []
        
        for theme, count in theme_counts.most_common(10):
            if count >= 2:  # 2回以上出現するテーマ
                common_themes.append({
                    'theme': theme,
                    'frequency': count,
                    'percentage': round((count / len(proposals)) * 100, 1)
                })
        
        return common_themes
    
    def _extract_japanese_keywords(self, text: str) -> List[str]:
        """日本語キーワードを抽出"""
        # 基本的なキーワード抽出（実際のプロジェクトでは形態素解析ライブラリを使用）
        keywords = []
        
        # 技術関連キーワード
        tech_keywords = ['AI', '人工知能', '機械学習', '自動化', 'システム', 'アプリ', 'ウェブ', 'データ', '分析', '最適化']
        for keyword in tech_keywords:
            if keyword in text:
                keywords.append(keyword)
        
        # ビジネス関連キーワード
        business_keywords = ['効率化', 'コスト削減', '収益', 'マーケティング', '顧客', 'サービス', 'プロセス', '改善']
        for keyword in business_keywords:
            if keyword in text:
                keywords.append(keyword)
        
        # その他の重要キーワード
        other_keywords = ['IoT', 'クラウド', 'セキュリティ', 'モバイル', 'リアルタイム', '可視化']
        for keyword in other_keywords:
            if keyword in text:
                keywords.append(keyword)
        
        return keywords
    
    def _identify_innovative_solutions(self, proposals: List[Proposal]) -> List[Dict[str, Any]]:
        """革新的解決案を特定"""
        innovative_solutions = []
        
        innovation_keywords = ['AI', '人工知能', '機械学習', 'IoT', 'ブロックチェーン', '自動化', '新技術', '革新的']
        
        for proposal in proposals:
            text = proposal.conclusion + ' ' + proposal.reasoning
            innovation_score = sum(1 for keyword in innovation_keywords if keyword in text)
            
            if innovation_score >= 2:  # 2つ以上の革新キーワードを含む
                innovative_solutions.append({
                    'proposal_id': proposal.id,
                    'innovation_score': innovation_score,
                    'key_innovations': [kw for kw in innovation_keywords if kw in text],
                    'summary': proposal.conclusion[:100] + '...' if len(proposal.conclusion) > 100 else proposal.conclusion
                })
        
        return sorted(innovative_solutions, key=lambda x: x['innovation_score'], reverse=True)
    
    
    def _generate_insights(self) -> List[Dict[str, Any]]:
        """洞察を生成"""
        insights = []
        
        for proposal in self.proposals:
            text = proposal.conclusion + ' ' + proposal.reasoning
            
            # デバッグログ
            print(f"\n=== 提案ID {proposal.id} の分析 ===")
            print(f"rating: {proposal.rating}, rating_count: {proposal.rating_count}")
            
            # スコア計算（評価とコメント数を考慮）
            innovation_score = self._calculate_innovation_score(proposal, text)
            insightfulness_score = self._calculate_insightfulness_score(proposal)
            impact_score = self._calculate_impact_score(proposal, text)
            
            print(f"革新性スコア: {innovation_score}")
            print(f"支持率スコア: {insightfulness_score}")
            print(f"影響度スコア: {impact_score}")
            
            insights.append({
                'proposal_id': proposal.id,
                'innovation_score': innovation_score,
                'insightfulness_score': insightfulness_score,
                'impact_score': impact_score,
                'key_themes': self._extract_proposal_themes(text),
                'strengths': self._identify_strengths(text),
                'concerns': self._identify_concerns(text)
            })
        
        return insights
    
    def _calculate_insightfulness_score(self, proposal) -> float:
        """支持率スコアを計算（示唆性評価から）"""
        from proposals.models import ProposalEvaluation
        from django.db.models import Avg
        
        evaluations = ProposalEvaluation.objects.filter(proposal=proposal)
        
        if evaluations.count() == 0:
            return 0.5  # デフォルト値（評価なし）
        
        # insight_scoreの平均を計算（1-5の範囲）
        avg_insight = evaluations.aggregate(Avg('insight_score'))['insight_score__avg']
        
        if avg_insight is None:
            return 0.5  # デフォルト値
        
        # 1-5を0-1に正規化
        insightfulness = (avg_insight - 1) / 4  # 1→0.0, 3→0.5, 5→1.0
        
        return insightfulness
    
    def _calculate_innovation_score(self, proposal, text: str) -> float:
        """独創性スコアを計算（評価から）"""
        from proposals.models import ProposalEvaluation
        from django.db.models import Avg
        
        evaluations = ProposalEvaluation.objects.filter(proposal=proposal)
        
        if evaluations.count() == 0:
            return 0.5  # デフォルト値（評価なし）
        
        # scoreの平均を計算（0-2の範囲: Yes=0, Maybe=1, No=2）
        avg_score = evaluations.aggregate(Avg('score'))['score__avg']
        
        if avg_score is None:
            return 0.5  # デフォルト値
        
        # 0-2を0-1に正規化
        innovation = avg_score / 2  # 0（全員がYes）→0.0, 1（平均Maybe）→0.5, 2（全員がNo）→1.0
        
        print(f"  独創性スコア: {innovation:.2f} (評価{evaluations.count()}件、平均{avg_score:.2f}/2)")
        
        return innovation
    
    
    def _calculate_impact_score(self, proposal, text: str) -> float:
        """
        影響度スコアを計算（議論の活発さから）
        
        評価基準:
        1. コメント数（50%）: 議論の量を表す
        2. 参加者の多様性（30%）: 議論の広がりを表す
        3. コメントの平均長さ（20%）: コメントの質を表す
        """
        from proposals.models import ProposalComment
        
        comments = ProposalComment.objects.filter(proposal=proposal, is_deleted=False)
        comment_count = comments.count()
        
        if comment_count == 0:
            return 0.0
        
        # 1. コメント数スコア（0-0.5）: コメント数の対数スケールで評価
        # 理由: 1→10コメントの増加は10→20より価値が高い
        import math
        comment_score = min(math.log(comment_count + 1) / math.log(31), 1.0) * 0.5  # 30コメントで最大
        
        # 2. 参加者の多様性スコア（0-0.3）: ユニークなコメンター数
        unique_commenters = comments.values('commenter').distinct().count()
        # 対数スケール: 多様性も同様に初期の増加が重要
        diversity_score = min(math.log(unique_commenters + 1) / math.log(16), 1.0) * 0.3  # 15人で最大
        
        # 3. コメントの平均長さスコア（0-0.2）
        total_length = 0
        for comment in comments:
            conclusion_length = len(comment.conclusion) if comment.conclusion else 0
            reasoning_length = len(comment.reasoning) if comment.reasoning else 0
            total_length += conclusion_length + reasoning_length
        
        avg_length = total_length / comment_count if comment_count > 0 else 0
        # 対数スケール: 500文字で最大
        length_score = min(math.log(avg_length + 1) / math.log(501), 1.0) * 0.2
        
        # 合計スコア
        total_impact = comment_score + diversity_score + length_score
        
        # デバッグログ
        print(f"  コメント数: {comment_count}, 参加者: {unique_commenters}, 平均長: {avg_length:.0f}文字")
        print(f"  スコア詳細: コメント={comment_score:.3f}, 多様性={diversity_score:.3f}, 長さ={length_score:.3f}")
        print(f"  合計影響度スコア: {total_impact:.3f}")
        
        return min(total_impact, 1.0)
    
    def _extract_proposal_themes(self, text: str) -> List[str]:
        """提案のテーマを抽出"""
        themes = []
        if 'AI' in text or '人工知能' in text:
            themes.append('AI・人工知能')
        if '自動化' in text:
            themes.append('自動化')
        if 'データ' in text or '分析' in text:
            themes.append('データ分析')
        if '効率' in text or '最適化' in text:
            themes.append('効率化')
        return themes
    
    def _identify_strengths(self, text: str) -> List[str]:
        """強みを特定"""
        strengths = []
        if '低コスト' in text:
            strengths.append('コスト効率')
        if '短期間' in text or '迅速' in text:
            strengths.append('迅速な実装')
        if 'シンプル' in text or '簡単' in text:
            strengths.append('実装の容易さ')
        if '検証済み' in text or '実績' in text:
            strengths.append('実績・信頼性')
        return strengths
    
    def _identify_concerns(self, text: str) -> List[str]:
        """懸念点を特定"""
        concerns = []
        if '高コスト' in text:
            concerns.append('コスト面')
        if '長期間' in text or '時間' in text:
            concerns.append('実装期間')
        if '複雑' in text or '困難' in text:
            concerns.append('技術的複雑さ')
        if '未検証' in text or 'リスク' in text:
            concerns.append('リスク・不確実性')
        return concerns
    
    def _generate_summaries(self, basic_stats: Dict, content_analysis: Dict, insights: List[Dict]) -> Dict[str, str]:
        """まとめ文を生成"""
        
        executive_summary = self._generate_executive_summary(basic_stats, content_analysis)
        detailed_analysis = self._generate_detailed_analysis(content_analysis, insights)
        recommendations = self._generate_recommendations(content_analysis, insights)
        
        return {
            'executive_summary': executive_summary,
            'detailed_analysis': detailed_analysis,
            'recommendations': recommendations
        }
    
    def _generate_executive_summary(self, basic_stats: Dict, content_analysis: Dict) -> str:
        """エグゼクティブサマリーを生成（シンプル版）"""
        total_proposals = basic_stats['total_proposals']
        unique_proposers = basic_stats['unique_proposers']
        
        summary = f"本課題に対して{unique_proposers}名の提案者から合計{total_proposals}件の解決案が提出されました。"
        
        if content_analysis['common_themes']:
            top_theme = content_analysis['common_themes'][0]
            summary += f"\n最も多く提案されたテーマは「{top_theme['theme']}」です。"
        
        return summary
    
    def _generate_detailed_analysis(self, content_analysis: Dict, insights: List[Dict]) -> str:
        """詳細分析を生成（簡素化）"""
        analysis = ""
        
        # 共通テーマのみ記載
        if content_analysis['common_themes']:
            analysis += "【共通テーマ】\n"
            for theme in content_analysis['common_themes'][:5]:
                analysis += f"・{theme['theme']}: {theme['frequency']}回言及 ({theme['percentage']}%)\n"
        
        return analysis
    
    def _generate_recommendations(self, content_analysis: Dict, insights: List[Dict]) -> str:
        """推奨事項を生成（空文字列を返す）"""
        return ""
    
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
                    'key_themes': insight_data['key_themes'],
                    'strengths': insight_data['strengths'],
                    'concerns': insight_data['concerns']
                }
            )


def analyze_challenge_on_deadline(challenge_id: int):
    """期限切れ時に自動分析を実行"""
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
    
    def _lightweight_clustering(self, proposals: List[Proposal]) -> Dict[str, Any]:
        """軽量なクラスタリング（AIモデルを使用しない）"""
        import re
        from collections import defaultdict
        import numpy as np
        
        print("軽量クラスタリング開始")
        
        # テキストの前処理とキーワード抽出
        texts = []
        for proposal in proposals:
            text = f"{proposal.conclusion} {proposal.reasoning}"
            # 日本語のキーワードを抽出
            cleaned_text = re.sub(r'[^\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF\w\s]', ' ', text)
            texts.append(cleaned_text.lower())
        
        # キーワードベースの類似度計算
        all_words = set()
        for text in texts:
            words = text.split()
            all_words.update(words)
        
        # 各テキストの単語頻度ベクトルを作成
        word_vectors = []
        for text in texts:
            words = text.split()
            vector = [words.count(word) for word in all_words]
            word_vectors.append(vector)
        
        # コサイン類似度でクラスタリング
        from sklearn.cluster import KMeans
        from sklearn.metrics.pairwise import cosine_similarity
        
        # 適切なクラスタ数を決定（2-5の範囲）
        n_clusters = min(max(2, len(proposals) // 10), 5)
        
        # K-meansクラスタリング
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(word_vectors)
        
        print(f"クラスタリング完了: {n_clusters}クラスタ生成")
        
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
        print(f"座標サンプル: {coordinates_2d[:5]}")
        
        # クラスタごとに中心を調整
        coordinates_2d = self._adjust_cluster_positions(coordinates_2d, cluster_labels)
        print(f"クラスタ調整後座標範囲: X({coordinates_2d[:, 0].min():.3f}-{coordinates_2d[:, 0].max():.3f}), Y({coordinates_2d[:, 1].min():.3f}-{coordinates_2d[:, 1].max():.3f})")
        
        # 独創性スコアに基づいて中心からの距離を調整
        coordinates_2d = self._adjust_positions_by_innovation(proposals, coordinates_2d)
        print(f"独創性調整後座標範囲: X({coordinates_2d[:, 0].min():.3f}-{coordinates_2d[:, 0].max():.3f}), Y({coordinates_2d[:, 1].min():.3f}-{coordinates_2d[:, 1].max():.3f})")
        
        # 結果を整形
        result = self._format_results(proposals, coordinates_2d, cluster_labels)
        
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
    
    def _adjust_cluster_positions(self, coordinates, cluster_labels):
        """
        クラスタごとの配置を調整してより良い分散を実現
        """
        import numpy as np
        
        adjusted = coordinates.copy()
        unique_clusters = np.unique(cluster_labels)
        
        # 各クラスタの重心を計算
        cluster_centroids = {}
        for cluster_id in unique_clusters:
            cluster_mask = cluster_labels == cluster_id
            cluster_points = coordinates[cluster_mask]
            cluster_centroids[cluster_id] = cluster_points.mean(axis=0)
        
        # クラスタ数を考慮して理想的な配置を計算
        n_clusters = len(unique_clusters)
        if n_clusters <= 1:
            return adjusted
        
        # 円形にクラスタ重心を配置（より良い分散のため）
        ideal_centroids = {}
        for i, cluster_id in enumerate(unique_clusters):
            angle = 2 * np.pi * i / n_clusters
            # 0.2-0.8の範囲で円形配置
            ideal_centroids[cluster_id] = np.array([
                0.5 + 0.3 * np.cos(angle),
                0.5 + 0.3 * np.sin(angle)
            ])
        
        # 各クラスタの点を理想的な位置に移動
        for cluster_id in unique_clusters:
            cluster_mask = cluster_labels == cluster_id
            cluster_points = adjusted[cluster_mask]
            
            if len(cluster_points) > 0:
                # 現在のクラスタ重心
                current_centroid = cluster_points.mean(axis=0)
                # 理想的なクラスタ重心
                ideal_centroid = ideal_centroids[cluster_id]
                
                # 移動ベクトル
                move_vector = ideal_centroid - current_centroid
                
                # クラスタ内の各点を移動（ランダムなばらつきを追加）
                for i, is_in_cluster in enumerate(cluster_mask):
                    if is_in_cluster:
                        # 基本的な移動
                        adjusted[i] += move_vector * 0.8
                        
                        # クラスタ内でのランダムなばらつきを追加
                        if len(cluster_points) > 1:
                            # 一貫した結果のためシードを設定
                            np.random.seed(42 + cluster_id * 100 + i)
                            noise = np.random.normal(0, 0.05, 2)
                            adjusted[i] += noise
        
        # 0-1の範囲にクリップ
        adjusted = np.clip(adjusted, 0, 1)
        
        return adjusted
    
    def _adjust_positions_by_innovation(self, proposals, coordinates):
        """
        独創性スコアに基づいて座標を調整
        中央(0.5, 0.5)からの距離を独創性スコアに比例させる
        
        独創性が高い（スコアが高い）→ 中心から遠く
        独創性が低い（スコアが低い）→ 中心に近く
        """
        import numpy as np
        from proposals.models import ProposalEvaluation
        from django.db.models import Avg
        
        adjusted = coordinates.copy()
        center = np.array([0.5, 0.5])
        
        # 各提案の独創性スコアを計算
        innovation_scores = []
        has_evaluations = []
        for proposal in proposals:
            evaluations = ProposalEvaluation.objects.filter(proposal=proposal)
            
            if evaluations.count() == 0:
                # 評価がない場合は中間値（0.5）
                innovation_scores.append(0.5)
                has_evaluations.append(False)
            else:
                # scoreの平均を計算（0-2の範囲: Yes=0, Maybe=1, No=2）
                avg_score = evaluations.aggregate(Avg('score'))['score__avg']
                if avg_score is None:
                    innovation_scores.append(0.5)
                    has_evaluations.append(False)
                else:
                    # 0-2を0-1に正規化（Noが多い=独創的=1.0）
                    innovation_scores.append(avg_score / 2.0)
                    has_evaluations.append(True)
        
        innovation_scores = np.array(innovation_scores)
        
        # スコアの分布を確認
        evaluated_scores = [innovation_scores[i] for i, has_eval in enumerate(has_evaluations) if has_eval]
        unevaluated_scores = [innovation_scores[i] for i, has_eval in enumerate(has_evaluations) if not has_eval]
        
        print(f"独創性スコア範囲: {innovation_scores.min():.3f}-{innovation_scores.max():.3f}")
        if evaluated_scores:
            print(f"  評価済み({len(evaluated_scores)}件): {min(evaluated_scores):.3f}-{max(evaluated_scores):.3f}, 平均: {np.mean(evaluated_scores):.3f}")
        if unevaluated_scores:
            print(f"  未評価({len(unevaluated_scores)}件): すべて0.500（デフォルト値）")
        
        # 各点について、中心からの距離を独創性スコアに基づいて調整
        for i in range(len(adjusted)):
            # 現在の中心からの方向ベクトル
            direction = adjusted[i] - center
            current_distance = np.linalg.norm(direction)
            
            if current_distance > 0:
                # 独創性スコアに基づいて新しい距離を計算
                # innovation_score: 0.0（独創性低）→ 0.5（中間）→ 1.0（独創性高）
                # 距離の範囲: 0.05-0.48（最小5%、最大48%の距離）
                min_distance = 0.05
                max_distance = 0.48
                target_distance = min_distance + innovation_scores[i] * (max_distance - min_distance)
                
                # 方向は維持したまま、距離を調整
                direction_normalized = direction / current_distance
                adjusted[i] = center + direction_normalized * target_distance
        
        # 0-1の範囲にクリップ
        adjusted = np.clip(adjusted, 0, 1)
        
        return adjusted
    
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
    
    def _format_results(self, proposals: List[Proposal], coordinates_2d, cluster_labels) -> Dict[str, Any]:
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
                anon_name_obj = ChallengeUserAnonymousName.objects.filter(
                    challenge=challenge,
                    user=proposal.proposer
                ).select_related('anonymous_name').first()
                if anon_name_obj and anon_name_obj.anonymous_name:
                    anonymous_name = anon_name_obj.anonymous_name.name
            except Exception as e:
                print(f"匿名名取得エラー: {e}")
            
            # コメント数を取得（影響度の指標）
            comment_count = ProposalComment.objects.filter(
                proposal=proposal,
                is_deleted=False
            ).count()
            
            # 基本データ
            coordinate_item = {
                'proposal_id': proposal.id,
                'x': float(coordinates_2d[i][0]),
                'y': float(coordinates_2d[i][1]),
                'cluster': int(cluster_labels[i]),
                'conclusion': proposal.conclusion,
                'proposer_name': proposer_name,
                'anonymous_name': anonymous_name,
                'comment_count': comment_count  # 影響度として使用
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
        
        # クラスタ情報を集計
        cluster_counter = Counter(cluster_labels)
        cluster_info = []
        for cluster_id, size in cluster_counter.items():
            # クラスタ内の解決案からテーマを抽出
            cluster_proposals = [p for p, label in zip(proposals, cluster_labels) if label == cluster_id]
            theme = self._extract_cluster_theme(cluster_proposals)
            
            cluster_info.append({
                'cluster_id': int(cluster_id),
                'size': size,
                'theme': theme
            })
        
        # 軸の意味を自動生成
        axis_labels = self._generate_axis_labels(proposals, coordinates_2d, cluster_labels)
        
        return {
            'coordinates': coordinates_data,
            'cluster_info': cluster_info,
            'total_clusters': len(cluster_counter),
            'axis_labels': axis_labels
        }
    
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
        軸の意味を推定
        左端/下端と右端/上端の解決案を比較して、対比を抽出
        """
        import re
        from collections import Counter
        
        # キーワード辞書（対比的な概念）
        keyword_pairs = [
            (['政策', '制度', '法律', '規制', '政府'], ['経済', '市場', '民間', '企業', '投資']),
            (['短期', '現在', '即効', '緊急'], ['長期', '将来', '未来', '持続']),
            (['保守', '維持', '継続', '伝統'], ['革新', '改革', '変革', '刷新']),
            (['国内', '内需', '地方', '日本'], ['国際', '輸出', 'グローバル', '海外']),
            (['増税', '財源', '負担', '課税'], ['減税', '支援', '補助', '優遇']),
            (['個人', '消費者', '家計', '国民'], ['企業', '産業', '事業者', '法人']),
            (['構造', 'システム', '仕組み', '制度'], ['運用', '実行', '実施', '推進']),
        ]
        
        # 左端/下端のキーワードを抽出
        left_text = ' '.join([p.conclusion + ' ' + p.reasoning for p in left_proposals])
        left_keywords = re.findall(r'[一-龠々ァ-ヶー]{2,}', left_text)
        
        # 右端/上端のキーワードを抽出
        right_text = ' '.join([p.conclusion + ' ' + p.reasoning for p in right_proposals])
        right_keywords = re.findall(r'[一-龠々ァ-ヶー]{2,}', right_text)
        
        # 最も適切な対比を見つける
        best_pair = None
        best_score = 0
        
        for left_words, right_words in keyword_pairs:
            left_match = sum(1 for kw in left_keywords if any(w in kw for w in left_words))
            right_match = sum(1 for kw in right_keywords if any(w in kw for w in right_words))
            score = left_match + right_match
            
            if score > best_score:
                best_score = score
                best_pair = (left_words[0], right_words[0])
        
        # マッチしなければデフォルト
        if best_pair:
            return {
                'left': best_pair[0] + '的',
                'right': best_pair[1] + '的'
            }
        else:
            return {
                'left': 'タイプA',
                'right': 'タイプB'
            }
    
    def _extract_cluster_theme(self, proposals: List[Proposal]) -> str:
        """クラスタ内の解決案から共通テーマを抽出"""
        # 簡易的にキーワードの頻度で判定
        from collections import Counter
        import re
        
        # 全ての結論と理由からキーワードを抽出
        all_words = []
        for proposal in proposals:
            text = f"{proposal.conclusion} {proposal.reasoning}"
            # 簡易的な形態素解析（3文字以上のカタカナ・漢字を抽出）
            words = re.findall(r'[ァ-ヶー]{3,}|[一-龠々]{3,}', text)
            all_words.extend(words)
        
        # 最頻出のキーワードをテーマとする
        if all_words:
            word_counter = Counter(all_words)
            most_common = word_counter.most_common(1)[0]
            return most_common[0]
        
        return f"クラスタ（{len(proposals)}件）"
    
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
            
            # コメント数を取得
            from proposals.models import ProposalComment
            comment_count = ProposalComment.objects.filter(
                proposal=proposal,
                is_deleted=False
            ).count()
            
            coordinates_data.append({
                'proposal_id': proposal.id,
                'x': float(x),
                'y': float(y),
                'cluster': 0,
                'conclusion': proposal.conclusion,
                'proposer_name': proposer_name,
                'comment_count': comment_count
            })
        
        return {
            'coordinates': coordinates_data,
            'cluster_info': [{'cluster_id': 0, 'size': len(proposals), 'theme': '全解決案'}],
            'total_clusters': 1,
            'axis_labels': {
                'x_axis': {'left': 'タイプA', 'right': 'タイプB'},
                'y_axis': {'left': 'タイプC', 'right': 'タイプD'}
            }
        }
