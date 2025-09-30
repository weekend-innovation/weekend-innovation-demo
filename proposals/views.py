from rest_framework import generics, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
import random
import logging
from .models import Proposal, AnonymousName
from challenges.models import Challenge
from .serializers import (
    ProposalSerializer, ProposalCreateSerializer, ProposalListSerializer
)

logger = logging.getLogger(__name__)

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
            return Proposal.objects.filter(proposer=user)
        elif user.user_type == 'contributor':
            # 投稿者: 自分の課題に対する提案のみ
            return Proposal.objects.filter(
                challenge__contributor=user
            )
        
        return Proposal.objects.none()
    
    def perform_create(self, serializer):
        """提案作成時の処理"""
        try:
            logger.debug(f"Proposal creation started for user: {self.request.user.id}")
            user = self.request.user
            
            # 提案者のみ作成可能
            if user.user_type != 'proposer':
                logger.warning(f"Non-proposer user {user.id} attempted to create proposal")
                raise permissions.PermissionDenied("提案者のみ提案を作成できます。")
            
            # 1課題1提案制限の確認と既存提案の削除
            challenge_id = serializer.validated_data.get('challenge').id
            logger.debug(f"Challenge ID: {challenge_id}")
            
            existing_proposals = Proposal.objects.filter(
                proposer=user,
                challenge_id=challenge_id
            ).order_by('-created_at')
            
            if existing_proposals.exists():
                logger.warning(f"User {user.id} already has {existing_proposals.count()} proposal(s) for challenge {challenge_id}")
                
                # 既存の提案を全て削除（最新の1つ以外）
                proposals_to_delete = existing_proposals[1:]  # 最新以外
                for proposal in proposals_to_delete:
                    logger.info(f"Deleting existing proposal {proposal.id} for user {user.id}, challenge {challenge_id}")
                    proposal.delete()
                
                # 最新の提案も削除（完全に新しい提案で置き換え）
                if existing_proposals.exists():
                    latest_proposal = existing_proposals.first()
                    logger.info(f"Deleting latest proposal {latest_proposal.id} for user {user.id}, challenge {challenge_id}")
                    latest_proposal.delete()
            
            # 匿名名をランダムに割り当て
            anonymous_name = self.get_random_anonymous_name()
            logger.debug(f"Selected anonymous name: {anonymous_name}")
            
            serializer.save(
                proposer=user,
                anonymous_name=anonymous_name,
                is_anonymous=True
            )
            logger.info(f"Proposal created successfully for user {user.id}, challenge {challenge_id}")
            
        except Exception as e:
            logger.error(f"Error in perform_create: {str(e)}", exc_info=True)
            raise
    
    def get_random_anonymous_name(self):
        """ランダムな匿名名を取得"""
        anonymous_names = list(AnonymousName.objects.all())
        if anonymous_names:
            return random.choice(anonymous_names)
        return None

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
            return Proposal.objects.filter(proposer=user)
        elif user.user_type == 'contributor':
            # 投稿者: 自分の課題に対する提案のみ閲覧可能
            return Proposal.objects.filter(
                challenge__contributor=user
            )
        
        return Proposal.objects.none()
    
    def get_object(self):
        """オブジェクト取得時の処理"""
        obj = super().get_object()
        
        # 提案者の場合、更新・削除のみ可能
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            if self.request.user.user_type != 'proposer':
                raise permissions.PermissionDenied("提案者のみ提案を編集・削除できます。")
        
        return obj

class ProposalByChallengeView(generics.ListAPIView):
    """
    課題別提案一覧取得API
    特定の課題に対する提案一覧を取得
    """
    serializer_class = ProposalListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """指定された課題の提案一覧を返す"""
        challenge_id = self.kwargs['challenge_id']
        user = self.request.user
        
        # 課題の存在確認と権限チェック
        challenge = get_object_or_404(
            Challenge,
            id=challenge_id
        )
        
        # 投稿者の場合、自分の課題の提案のみ閲覧可能
        if user.user_type == 'contributor':
            if challenge.contributor != user:
                raise permissions.PermissionDenied("自分の課題の提案のみ閲覧できます。")
        # 提案者の場合、自分の提案済み課題の提案のみ閲覧可能
        elif user.user_type == 'proposer':
            # ユーザーがこの課題に提案しているかチェック
            user_proposal = Proposal.objects.filter(
                proposer=user,
                challenge_id=challenge_id
            ).first()
            
            if not user_proposal:
                raise permissions.PermissionDenied("解決案を投稿すると、他の提案者の解決案も閲覧できるようになります。")
        
        return Proposal.objects.filter(challenge_id=challenge_id)

class UserProposalForChallengeView(generics.ListAPIView):
    """
    ユーザーの特定課題への提案状況確認API
    提案者が特定の課題に対して既に提案しているかチェック
    """
    serializer_class = ProposalListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """ユーザーの特定課題への提案を返す"""
        challenge_id = self.kwargs['challenge_id']
        user = self.request.user
        
        # 提案者のみ利用可能
        if user.user_type != 'proposer':
            raise permissions.PermissionDenied("提案者のみ利用できます。")
        
        # 課題の存在確認
        get_object_or_404(
            Challenge,
            id=challenge_id
        )
        
        return Proposal.objects.filter(
            proposer=user,
            challenge_id=challenge_id
        )