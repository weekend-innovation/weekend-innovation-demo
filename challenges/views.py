from rest_framework import generics, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Challenge
from .serializers import ChallengeSerializer, ChallengeCreateSerializer, ChallengeListSerializer

class ChallengeListCreateView(generics.ListCreateAPIView):
    """
    課題一覧取得・作成API
    投稿者: 自分が投稿した課題のみ表示・作成可能
    提案者: 選出された課題のみ表示可能（作成不可）
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """HTTPメソッドに応じてシリアライザーを切り替え"""
        if self.request.method == 'POST':
            return ChallengeCreateSerializer
        return ChallengeListSerializer
    
    def get_queryset(self):
        """ユーザータイプに応じてクエリセットを返す"""
        user = self.request.user
        
        if user.user_type == 'contributor':
            # 投稿者: 自分が投稿した課題のみ
            return Challenge.objects.filter(contributor=user)
        elif user.user_type == 'proposer':
            # 提案者: 選出された課題のみ表示
            # TODO: 選出機能実装後に selections__proposer=user を追加
            return Challenge.objects.filter(status='open')
        
        return Challenge.objects.none()
    
    def perform_create(self, serializer):
        """課題作成時の処理"""
        user = self.request.user
        
        # 投稿者のみ作成可能
        if user.user_type != 'contributor':
            raise permissions.PermissionDenied("投稿者のみ課題を作成できます。")
        
        serializer.save(contributor=user)

class ChallengeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    課題詳細取得・更新・削除API
    投稿者: 自分の課題のみ操作可能
    提案者: 選出された課題のみ閲覧可能
    """
    serializer_class = ChallengeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """ユーザータイプに応じてクエリセットを返す"""
        user = self.request.user
        
        if user.user_type == 'contributor':
            # 投稿者: 自分の課題のみ
            return Challenge.objects.filter(contributor=user)
        elif user.user_type == 'proposer':
            # 提案者: 選出された課題のみ閲覧可能
            # TODO: 選出機能実装後に selections__proposer=user を追加
            return Challenge.objects.filter(status='open')
        
        return Challenge.objects.none()
    
    def get_object(self):
        """オブジェクト取得時の処理"""
        obj = super().get_object()
        
        # 投稿者の場合、更新・削除のみ可能
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            if self.request.user.user_type != 'contributor':
                raise permissions.PermissionDenied("投稿者のみ課題を編集・削除できます。")
        
        return obj
    
    def destroy(self, request, *args, **kwargs):
        """課題削除時の処理"""
        challenge = self.get_object()
        
        # 投稿者のみ削除可能
        if request.user.user_type != 'contributor':
            raise permissions.PermissionDenied("投稿者のみ課題を削除できます。")
        
        challenge.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ChallengeStatusUpdateView(generics.UpdateAPIView):
    """
    課題ステータス更新API
    投稿者のみ使用可能
    """
    serializer_class = ChallengeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """投稿者の課題のみ"""
        return Challenge.objects.filter(
            contributor=self.request.user,
            user_type='contributor'
        )
    
    def update(self, request, *args, **kwargs):
        """ステータス更新処理"""
        challenge = self.get_object()
        
        # 投稿者のみ更新可能
        if request.user.user_type != 'contributor':
            raise permissions.PermissionDenied("投稿者のみ課題ステータスを更新できます。")
        
        new_status = request.data.get('status')
        
        # ステータス変更の妥当性チェック
        if new_status not in ['open', 'closed', 'completed']:
            return Response(
                {'error': '無効なステータスです。'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        challenge.status = new_status
        challenge.save()
        
        serializer = self.get_serializer(challenge)
        return Response(serializer.data)

class PublicChallengeListView(generics.ListAPIView):
    """
    公開課題一覧API
    認証不要で全ての募集中課題を表示
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = ChallengeListSerializer
    
    def get_queryset(self):
        """募集中の課題のみ表示"""
        return Challenge.objects.filter(status='open')