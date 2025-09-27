from rest_framework import generics, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Proposal, ProposalComment, ProposalEvaluation
from .serializers import (
    ProposalSerializer, ProposalCreateSerializer, ProposalListSerializer,
    ProposalCommentSerializer, ProposalCommentCreateSerializer,
    ProposalEvaluationSerializer, ProposalEvaluationCreateSerializer
)

class ProposalListCreateView(generics.ListCreateAPIView):
    """
    提案一覧取得・作成API
    提案者: 自分の提案のみ表示・作成可能
    投稿者: 自分の課題に対する提案を表示可能
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """HTTPメソッドに応じてシリアライザーを切り替え"""
        if self.request.method == 'POST':
            return ProposalCreateSerializer
        return ProposalListSerializer
    
    def get_queryset(self):
        """ユーザータイプに応じてクエリセットを返す"""
        user = self.request.user
        
        if user.user_type == 'proposer':
            # 提案者: 自分の提案のみ
            return Proposal.objects.filter(proposer=user, is_deleted=False)
        elif user.user_type == 'contributor':
            # 投稿者: 自分の課題に対する提案のみ
            return Proposal.objects.filter(
                challenge__contributor=user,
                is_deleted=False
            )
        
        return Proposal.objects.none()
    
    def perform_create(self, serializer):
        """提案作成時の処理"""
        user = self.request.user
        
        # 提案者のみ作成可能
        if user.user_type != 'proposer':
            raise permissions.PermissionDenied("提案者のみ提案を作成できます。")
        
        serializer.save(proposer=user)

class ProposalDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    提案詳細取得・更新・削除API
    提案者: 自分の提案のみ操作可能
    投稿者: 自分の課題に対する提案のみ閲覧可能
    """
    serializer_class = ProposalSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """ユーザータイプに応じてクエリセットを返す"""
        user = self.request.user
        
        if user.user_type == 'proposer':
            # 提案者: 自分の提案のみ
            return Proposal.objects.filter(proposer=user, is_deleted=False)
        elif user.user_type == 'contributor':
            # 投稿者: 自分の課題に対する提案のみ
            return Proposal.objects.filter(
                challenge__contributor=user,
                is_deleted=False
            )
        
        return Proposal.objects.none()
    
    def get_object(self):
        """オブジェクト取得時の処理"""
        obj = super().get_object()
        
        # 投稿者の場合、閲覧のみ可能
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            if self.request.user.user_type != 'proposer':
                raise permissions.PermissionDenied("提案者のみ提案を編集・削除できます。")
        
        return obj
    
    def destroy(self, request, *args, **kwargs):
        """提案削除時の処理（論理削除）"""
        proposal = self.get_object()
        
        # 提案者のみ削除可能
        if request.user.user_type != 'proposer':
            raise permissions.PermissionDenied("提案者のみ提案を削除できます。")
        
        proposal.is_deleted = True
        proposal.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ProposalCommentListCreateView(generics.ListCreateAPIView):
    """
    提案コメント一覧取得・作成API
    提案者・投稿者のみ使用可能
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """HTTPメソッドに応じてシリアライザーを切り替え"""
        if self.request.method == 'POST':
            return ProposalCommentCreateSerializer
        return ProposalCommentSerializer
    
    def get_queryset(self):
        """提案IDに基づいてコメントを取得"""
        proposal_id = self.kwargs.get('proposal_id')
        return ProposalComment.objects.filter(
            proposal_id=proposal_id,
            is_deleted=False
        )
    
    def perform_create(self, serializer):
        """コメント作成時の処理"""
        proposal_id = self.kwargs.get('proposal_id')
        proposal = get_object_or_404(Proposal, id=proposal_id)
        
        # 提案者・投稿者のみコメント可能
        user = self.request.user
        if not (user.user_type == 'proposer' or 
                (user.user_type == 'contributor' and proposal.challenge.contributor == user)):
            raise permissions.PermissionDenied("コメントの投稿権限がありません。")
        
        serializer.save(commenter=self.request.user, proposal=proposal)

class ProposalEvaluationListCreateView(generics.ListCreateAPIView):
    """
    提案評価一覧取得・作成API
    提案者・投稿者のみ使用可能
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """HTTPメソッドに応じてシリアライザーを切り替え"""
        if self.request.method == 'POST':
            return ProposalEvaluationCreateSerializer
        return ProposalEvaluationSerializer
    
    def get_queryset(self):
        """提案IDに基づいて評価を取得"""
        proposal_id = self.kwargs.get('proposal_id')
        return ProposalEvaluation.objects.filter(proposal_id=proposal_id)
    
    def perform_create(self, serializer):
        """評価作成時の処理"""
        proposal_id = self.kwargs.get('proposal_id')
        proposal = get_object_or_404(Proposal, id=proposal_id)
        
        # 提案者・投稿者のみ評価可能
        user = self.request.user
        if not (user.user_type == 'proposer' or 
                (user.user_type == 'contributor' and proposal.challenge.contributor == user)):
            raise permissions.PermissionDenied("評価の投稿権限がありません。")
        
        serializer.save(evaluator=self.request.user, proposal=proposal)

class ProposalEvaluationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    提案評価詳細取得・更新・削除API
    評価者のみ操作可能
    """
    serializer_class = ProposalEvaluationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """評価者の評価のみ"""
        return ProposalEvaluation.objects.filter(evaluator=self.request.user)
    
    def get_object(self):
        """オブジェクト取得時の処理"""
        proposal_id = self.kwargs.get('proposal_id')
        evaluation_id = self.kwargs.get('pk')
        
        return get_object_or_404(
            ProposalEvaluation,
            id=evaluation_id,
            proposal_id=proposal_id,
            evaluator=self.request.user
        )

class ProposalByChallengeListView(generics.ListAPIView):
    """
    特定課題の提案一覧取得API
    課題の投稿者・選出された提案者のみ閲覧可能
    """
    serializer_class = ProposalListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """課題IDに基づいて提案を取得"""
        challenge_id = self.kwargs.get('challenge_id')
        user = self.request.user
        
        # 課題の投稿者または選出された提案者のみ閲覧可能
        # TODO: 選出機能実装後に selections__proposer=user を追加
        if user.user_type == 'contributor':
            return Proposal.objects.filter(
                challenge_id=challenge_id,
                challenge__contributor=user,
                is_deleted=False
            )
        elif user.user_type == 'proposer':
            return Proposal.objects.filter(
                challenge_id=challenge_id,
                is_deleted=False
            )
        
        return Proposal.objects.none()

class ProposalAdoptionView(generics.UpdateAPIView):
    """
    提案採用API
    課題の投稿者のみ使用可能
    """
    serializer_class = ProposalSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """課題の投稿者のみ"""
        return Proposal.objects.filter(
            challenge__contributor=self.request.user,
            is_deleted=False
        )
    
    def update(self, request, *args, **kwargs):
        """提案採用処理"""
        proposal = self.get_object()
        
        # 投稿者のみ採用可能
        if request.user.user_type != 'contributor':
            raise permissions.PermissionDenied("投稿者のみ提案を採用できます。")
        
        # 採用フラグを設定
        proposal.is_adopted = True
        proposal.save()
        
        serializer = self.get_serializer(proposal)
        return Response(serializer.data)