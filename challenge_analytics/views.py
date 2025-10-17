"""
課題分析・まとめ機能のAPIビュー
"""
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from challenges.models import Challenge
from .models import ChallengeAnalysis, ProposalInsight
from .serializers import ChallengeAnalysisSerializer, ProposalInsightSerializer
from .services import ChallengeAnalyzer

User = get_user_model()


class ChallengeAnalysisDetailView(generics.RetrieveAPIView):
    """課題分析結果の詳細取得"""
    
    serializer_class = ChallengeAnalysisSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        challenge_id = self.kwargs['challenge_id']
        challenge = get_object_or_404(Challenge, id=challenge_id)
        
        # 投稿者または提案者（自分が提案した課題）がアクセス可能
        user = self.request.user
        
        # 投稿者の場合：自分の課題のみ
        if user.user_type == 'contributor':
            if challenge.contributor != user:
                raise permissions.PermissionDenied("この分析結果にアクセスする権限がありません。")
        
        # 提案者の場合：自分が提案した課題のみ、かつ期限切れの課題のみ
        elif user.user_type == 'proposer':
            from proposals.models import Proposal
            
            # 期限切れチェック
            if challenge.status != 'closed':
                raise permissions.PermissionDenied("この課題はまだ期限切れではありません。")
            
            # 自分の提案が存在するかチェック
            has_proposal = Proposal.objects.filter(
                challenge=challenge,
                proposer=user
            ).exists()
            
            if not has_proposal:
                raise permissions.PermissionDenied("この課題に提案していないため、分析結果にアクセスできません。")
        else:
            raise permissions.PermissionDenied("この分析結果にアクセスする権限がありません。")
        
        analysis, created = ChallengeAnalysis.objects.get_or_create(
            challenge=challenge,
            defaults={'status': 'pending'}
        )
        
        # 分析が未完了の場合は実行（期限切れ課題のみ）
        if analysis.status in ['pending', 'failed'] and challenge.status == 'closed':
            try:
                analyzer = ChallengeAnalyzer(challenge_id)
                analysis = analyzer.analyze_challenge()
            except Exception as e:
                # エラーの場合でも既存の分析レコードを返す
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'分析の実行に失敗しました (課題ID: {challenge_id}): {str(e)}')
                # エラーを返さずに、pending状態の分析を返す
        
        return analysis


class ProposalInsightListView(generics.ListAPIView):
    """提案洞察の一覧取得"""
    
    serializer_class = ProposalInsightSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        challenge_id = self.kwargs['challenge_id']
        challenge = get_object_or_404(Challenge, id=challenge_id)
        
        # 投稿者のみアクセス可能
        if self.request.user.user_type != 'contributor' or challenge.contributor != self.request.user:
            raise permissions.PermissionDenied("この分析結果にアクセスする権限がありません。")
        
        analysis = get_object_or_404(ChallengeAnalysis, challenge=challenge)
        return ProposalInsight.objects.filter(analysis=analysis).order_by('-innovation_score', '-feasibility_score')


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def trigger_analysis(request, challenge_id):
    """分析の手動実行"""
    
    challenge = get_object_or_404(Challenge, id=challenge_id)
    
    # 投稿者のみ実行可能
    if request.user.user_type != 'contributor' or challenge.contributor != request.user:
        return Response(
            {'error': 'この分析を実行する権限がありません。'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        analyzer = ChallengeAnalyzer(challenge_id)
        analysis = analyzer.analyze_challenge()
        
        serializer = ChallengeAnalysisSerializer(analysis)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'分析の実行に失敗しました: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def analysis_status(request, challenge_id):
    """分析ステータスの確認"""
    
    challenge = get_object_or_404(Challenge, id=challenge_id)
    
    # 投稿者のみアクセス可能
    if request.user.user_type != 'contributor' or challenge.contributor != request.user:
        return Response(
            {'error': 'この分析結果にアクセスする権限がありません。'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        analysis = ChallengeAnalysis.objects.get(challenge=challenge)
        return Response({
            'status': analysis.status,
            'analyzed_at': analysis.analyzed_at,
            'total_proposals': analysis.total_proposals,
            'unique_proposers': analysis.unique_proposers
        })
    except ChallengeAnalysis.DoesNotExist:
        return Response({
            'status': 'not_started',
            'analyzed_at': None,
            'total_proposals': 0,
            'unique_proposers': 0
        })


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def reset_analysis(request, challenge_id):
    """分析をリセット（開発用）"""
    
    challenge = get_object_or_404(Challenge, id=challenge_id)
    user = request.user
    
    # 投稿者または提案者（自分が提案した課題）が実行可能
    has_permission = False
    
    if user.user_type == 'contributor' and challenge.contributor == user:
        has_permission = True
    elif user.user_type == 'proposer':
        # 自分が提案した課題かチェック
        from proposals.models import Proposal
        has_proposal = Proposal.objects.filter(
            challenge=challenge,
            proposer=user
        ).exists()
        if has_proposal:
            has_permission = True
    
    if not has_permission:
        return Response(
            {'error': 'この分析をリセットする権限がありません。'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        # 既存の分析を削除
        deleted_count, _ = ChallengeAnalysis.objects.filter(challenge=challenge).delete()
        
        return Response({
            'message': f'分析をリセットしました（削除件数: {deleted_count}）',
            'deleted_count': deleted_count
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'分析のリセットに失敗しました: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_proposal_clustering(request, challenge_id):
    """
    解決案のクラスタリング結果を取得
    AIを使用して解決案を類似度でグループ化し、2次元座標を返す
    """
    from proposals.models import Proposal
    from .services import ProposalClusteringService
    
    challenge = get_object_or_404(Challenge, id=challenge_id)
    user = request.user
    
    # 投稿者または選出された提案者のみアクセス可能
    is_contributor = user.user_type == 'contributor' and challenge.contributor == user
    is_selected_proposer = False
    
    if user.user_type == 'proposer':
        from selections.models import Selection
        # 選出されたユーザーかチェック
        selection = Selection.objects.filter(
            challenge=challenge,
            status='completed',
            selected_users=user
        ).first()
        is_selected_proposer = selection is not None
    
    if not is_contributor and not is_selected_proposer:
        return Response(
            {'error': 'この機能にアクセスする権限がありません。'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # 期限切れの課題のみ
    if challenge.status != 'closed':
        return Response(
            {'error': 'この機能は期限切れの課題のみ利用できます。'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # 解決案を取得（提案者のプロフィール情報も含める）
        proposals = list(Proposal.objects.filter(challenge=challenge).select_related('proposer', 'proposer__proposer_profile'))
        
        if len(proposals) < 2:
            return Response(
                {'error': '解決案が2件以上必要です。'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # クラスタリング実行
        clustering_service = ProposalClusteringService()
        result = clustering_service.cluster_proposals(proposals)
        
        # デバッグログ
        print(f"API返却クラスタ数: {result.get('total_clusters', 'N/A')}")
        print(f"API返却座標数: {len(result.get('coordinates', []))}")
        print(f"API返却コメント数サンプル: {[c.get('comment_count', 0) for c in result.get('coordinates', [])[:5]]}")
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'クラスタリングエラー (課題ID: {challenge_id}): {str(e)}')
        
        return Response(
            {'error': f'クラスタリングの実行に失敗しました: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )