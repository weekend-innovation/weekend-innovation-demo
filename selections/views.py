"""
選出機能のAPIビュー
選出の作成、実行、管理機能を提供
"""
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from .models import Selection, SelectionHistory, SelectionCriteria
from .serializers import (
    SelectionSerializer, SelectionCreateSerializer, SelectionUpdateSerializer,
    SelectionListSerializer, SelectionDetailSerializer, SelectionStatisticsSerializer,
    SelectionRequestSerializer, SelectionHistorySerializer, SelectionCriteriaSerializer
)
from .services import SelectionService

User = get_user_model()


class SelectionListCreateView(generics.ListCreateAPIView):
    """
    選出一覧取得・作成API
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return SelectionCreateSerializer
        return SelectionListSerializer
    
    def get_queryset(self):
        """ユーザータイプに応じて選出一覧を取得"""
        user = self.request.user
        
        if user.user_type == 'contributor':
            # 投稿者は自分が作成した選出のみ
            return Selection.objects.filter(contributor=user).order_by('-created_at')
        elif user.user_type == 'proposer':
            # 提案者は自分が選出された選出のみ
            return Selection.objects.filter(selected_users=user).order_by('-created_at')
        else:
            return Selection.objects.none()


class SelectionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    選出詳細取得・更新・削除API
    """
    serializer_class = SelectionDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """ユーザータイプに応じて選出を取得"""
        user = self.request.user
        
        if user.user_type == 'contributor':
            # 投稿者は自分が作成した選出のみ
            return Selection.objects.filter(contributor=user)
        elif user.user_type == 'proposer':
            # 提案者は自分が選出された選出のみ
            return Selection.objects.filter(selected_users=user)
        else:
            return Selection.objects.none()
    
    def perform_destroy(self, instance):
        """選出の削除（キャンセル）"""
        SelectionService.cancel_selection(
            instance, 
            reason="投稿者による削除"
        )


class SelectionExecuteView(APIView):
    """
    選出実行API
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """選出を実行"""
        if not request.user.is_authenticated:
            return Response(
                {'error': '認証が必要です'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if request.user.user_type != 'contributor':
            return Response(
                {'error': '投稿者のみ選出を実行できます'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = SelectionRequestSerializer(data=request.data, context={'request': request})
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from challenges.models import Challenge
            challenge = Challenge.objects.get(id=serializer.validated_data['challenge_id'])
            
            # 選出方法に応じて実行
            selection_method = serializer.validated_data.get('selection_method', 'random')
            required_count = serializer.validated_data['required_count']
            criteria = serializer.validated_data.get('selection_criteria', {})
            
            if selection_method == 'random':
                selection = SelectionService.random_selection(
                    challenge=challenge,
                    required_count=required_count,
                    criteria=criteria
                )
            elif selection_method == 'weighted':
                selection = SelectionService.weighted_selection(
                    challenge=challenge,
                    required_count=required_count,
                    criteria=criteria
                )
            else:
                return Response(
                    {'error': '無効な選出方法です'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 結果を返す
            result_serializer = SelectionDetailSerializer(selection)
            return Response(result_serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class SelectionHistoryView(generics.ListAPIView):
    """
    選出履歴取得API
    """
    serializer_class = SelectionHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """ユーザーに関連する選出履歴を取得"""
        user = self.request.user
        selection_id = self.kwargs.get('selection_id')
        
        if selection_id:
            selection = get_object_or_404(Selection, id=selection_id)
            
            # 権限チェック
            if user.user_type == 'contributor':
                if selection.contributor != user:
                    return SelectionHistory.objects.none()
            elif user.user_type == 'proposer':
                if not selection.selected_users.filter(id=user.id).exists():
                    return SelectionHistory.objects.none()
            
            return SelectionHistory.objects.filter(selection=selection).order_by('-created_at')
        
        # 全履歴の場合
        if user.user_type == 'contributor':
            selections = Selection.objects.filter(contributor=user)
            return SelectionHistory.objects.filter(
                selection__in=selections
            ).order_by('-created_at')
        elif user.user_type == 'proposer':
            selections = Selection.objects.filter(selected_users=user)
            return SelectionHistory.objects.filter(
                selection__in=selections
            ).order_by('-created_at')
        
        return SelectionHistory.objects.none()


class SelectionStatisticsView(APIView):
    """
    選出統計取得API
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """選出統計を取得"""
        try:
            stats = SelectionService.get_selection_statistics()
            serializer = SelectionStatisticsSerializer(stats)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SelectionCriteriaListView(generics.ListAPIView):
    """
    選出基準一覧取得API
    """
    serializer_class = SelectionCriteriaSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = SelectionCriteria.objects.filter(is_active=True)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def cancel_selection(request, selection_id):
    """
    選出キャンセルAPI
    """
    try:
        selection = get_object_or_404(Selection, id=selection_id)
        
        # 権限チェック
        if selection.contributor != request.user:
            return Response(
                {'error': 'この選出をキャンセルする権限がありません'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if selection.status == 'cancelled':
            return Response(
                {'error': 'この選出は既にキャンセルされています'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reason = request.data.get('reason', '')
        success = SelectionService.cancel_selection(selection, reason)
        
        if success:
            serializer = SelectionDetailSerializer(selection)
            return Response(serializer.data)
        else:
            return Response(
                {'error': '選出のキャンセルに失敗しました'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_eligible_users(request, challenge_id):
    """
    選出対象ユーザー取得API
    """
    try:
        from challenges.models import Challenge
        challenge = get_object_or_404(Challenge, id=challenge_id)
        
        # 権限チェック
        if challenge.contributor != request.user:
            return Response(
                {'error': 'この課題の選出対象ユーザーを取得する権限がありません'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        criteria = request.GET.get('criteria', {})
        if isinstance(criteria, str):
            import json
            try:
                criteria = json.loads(criteria)
            except:
                criteria = {}
        
        eligible_users = SelectionService.get_eligible_users(challenge, criteria)
        
        user_data = [
            {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': getattr(user.proposer_profile, 'full_name', '') if hasattr(user, 'proposer_profile') else '',
                'expertise': getattr(user.proposer_profile, 'expertise', '') if hasattr(user, 'proposer_profile') else '',
                'rating': getattr(user.proposer_profile, 'rating', 0) if hasattr(user, 'proposer_profile') else 0,
            }
            for user in eligible_users
        ]
        
        return Response({
            'eligible_users': user_data,
            'count': len(user_data)
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )