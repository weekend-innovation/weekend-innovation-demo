from rest_framework import generics, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
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
        from django.utils import timezone
        
        # 期限切れ課題を自動的にclosedに更新
        now = timezone.now()
        Challenge.objects.filter(
            status='open',
            deadline__lt=now
        ).update(status='closed')
        
        user = self.request.user
        
        if user.user_type == 'contributor':
            # 投稿者: 自分が投稿した課題のみ
            return Challenge.objects.filter(contributor=user)
        elif user.user_type == 'proposer':
            # 提案者: 選出された課題のみ表示（期限切れを含むすべての課題）
            from selections.models import Selection
            selected_challenges = Selection.objects.filter(
                selected_users=user,
                status='completed'
            ).values_list('challenge_id', flat=True)
            return Challenge.objects.filter(
                id__in=selected_challenges
            )
        
        return Challenge.objects.none()
    
    def perform_create(self, serializer):
        """課題作成時の処理"""
        user = self.request.user
        
        # 投稿者のみ作成可能
        if user.user_type != 'contributor':
            raise permissions.PermissionDenied("投稿者のみ課題を作成できます。")
        
        # 提案報酬を自動計算（バックエンドで計算式を隠蔽）
        validated_data = serializer.validated_data
        required_participants = validated_data['required_participants']
        
        # 共通関数を使用して計算
        reward_amount_yen = calculate_reward_amount(required_participants)
        
        validated_data['reward_amount'] = reward_amount_yen
        
        # 採用報酬は万円単位の入力を円単位に変換
        validated_data['adoption_reward'] = validated_data['adoption_reward'] * 10000
        
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
        from django.utils import timezone
        
        # 期限切れ課題を自動的にclosedに更新
        now = timezone.now()
        Challenge.objects.filter(
            status='open',
            deadline__lt=now
        ).update(status='closed')
        
        user = self.request.user
        
        if user.user_type == 'contributor':
            # 投稿者: 自分の課題のみ
            return Challenge.objects.filter(contributor=user)
        elif user.user_type == 'proposer':
            # 提案者: 選出された課題のみ閲覧可能（期限切れを含む）
            from selections.models import Selection
            selected_challenges = Selection.objects.filter(
                selected_users=user,
                status='completed'
            ).values_list('challenge_id', flat=True)
            return Challenge.objects.filter(id__in=selected_challenges)
        
        return Challenge.objects.none()
    
    def get_object(self):
        """オブジェクト取得時の処理"""
        obj = super().get_object()
        
        # 投稿者の場合、更新・削除のみ可能
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            if self.request.user.user_type != 'contributor':
                raise permissions.PermissionDenied("投稿者のみ課題を編集・削除できます。")
        
        return obj
    
    def perform_update(self, serializer):
        """課題更新時の処理"""
        # 万円単位の入力を円単位に変換
        validated_data = serializer.validated_data
        if 'reward_amount' in validated_data:
            validated_data['reward_amount'] = validated_data['reward_amount'] * 10000
        if 'adoption_reward' in validated_data:
            validated_data['adoption_reward'] = validated_data['adoption_reward'] * 10000
        
        serializer.save()
    
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

# 基礎報酬額の設定（グローバル定数）
# この値を変更すると、提案者への個人報酬も自動的に変更される
BASE_REWARD_PER_PERSON = 10000  # 1万円/人

# 提案者への支払い率
PROPOSER_PAYMENT_RATE = 0.6  # 60%

# 提案報酬計算の共通関数
def calculate_reward_amount(participants):
    """
    提案報酬総額を計算
    
    Args:
        participants: 選出人数
    
    Returns:
        int: 提案報酬総額（円）
    """
    # 基本報酬: BASE_REWARD_PER_PERSON/人（固定）
    base_reward_per_person = BASE_REWARD_PER_PERSON
    
    # 初期固定費: 3万円
    initial_setup_fee = 30000
    
    # システム運用費（段階的に変動）
    if participants <= 50:
        operational_cost_per_person = 5800
    elif participants <= 100:
        operational_cost_per_person = 5200
    elif participants <= 200:
        operational_cost_per_person = 5500
    elif participants <= 400:
        operational_cost_per_person = 5900
    elif participants <= 600:
        operational_cost_per_person = 6300
    else:
        operational_cost_per_person = 6700
    
    # 合計計算
    base_reward = participants * base_reward_per_person
    operational_cost = participants * operational_cost_per_person
    total = initial_setup_fee + base_reward + operational_cost
    
    return total

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def calculate_proposal_reward(request):
    """
    提案報酬を計算するAPI
    選出人数から提案報酬総額を計算して返す
    """
    participants = request.data.get('required_participants', 0)
    
    if not isinstance(participants, int) or participants < 50:
        return Response(
            {'error': '選出人数は50人以上である必要があります'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if participants > 770:
        return Response(
            {'error': '選出人数は770人以下である必要があります'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    reward_amount = calculate_reward_amount(participants)
    
    # 個人報酬の計算
    # 総額 ÷ 選出人数 × 60% = 基礎報酬額 × 60%
    individual_reward = BASE_REWARD_PER_PERSON * PROPOSER_PAYMENT_RATE
    
    return Response({
        'required_participants': participants,
        'reward_amount': reward_amount,
        'reward_amount_man': reward_amount / 10000,  # 万円単位
        'individual_reward': individual_reward,  # 個人報酬（円）
        'base_reward_per_person': BASE_REWARD_PER_PERSON,  # 基礎報酬額（円）
        'payment_rate': PROPOSER_PAYMENT_RATE  # 支払い率
    })