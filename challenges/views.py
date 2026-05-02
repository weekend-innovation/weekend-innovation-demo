import math
from datetime import timedelta
from rest_framework import generics, permissions, status, serializers
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from proposals.models import Proposal
from mvp_project.limits import MAX_SELECTION_PARTICIPANTS

from .models import Challenge, MAX_TOTAL_DAYS, MIN_TOTAL_DAYS
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
        from django.db.models import Case, When, Value, IntegerField, Q, Exists, OuterRef
        from proposals.models import Proposal
        from selections.models import UserEvaluationCompletion
        
        # 期限切れ課題を自動的にclosedに更新
        now = timezone.now()
        Challenge.objects.filter(
            status='open',
            deadline__lt=now
        ).update(status='closed')
        
        user = self.request.user
        
        if user.user_type == 'contributor':
            # 投稿者: 自分が投稿した課題のみ
            queryset = Challenge.objects.filter(contributor=user)
            
            # 投稿者の並び順: アクティブな課題を優先、その後期限が近い順
            queryset = queryset.annotate(
                priority_order=Case(
                    # アクティブな課題（提案期間、編集期間、評価期間）
                    When(
                        Q(proposal_deadline__gte=now) |
                        Q(edit_deadline__gte=now, proposal_deadline__lt=now) |
                        Q(evaluation_deadline__gte=now, edit_deadline__lt=now),
                        then=Value(1)
                    ),
                    # 期限切れ
                    default=Value(2),
                    output_field=IntegerField(),
                )
            ).order_by('priority_order', 'deadline')
            
            return queryset
            
        elif user.user_type == 'proposer':
            # 提案者: 選出された課題のみ表示
            from selections.models import Selection
            selected_challenges = Selection.objects.filter(
                selected_users=user,
                status='completed'
            ).values_list('challenge_id', flat=True)
            
            queryset = Challenge.objects.filter(id__in=selected_challenges)
            
            # 提案済みかどうかのサブクエリ
            has_proposed = Proposal.objects.filter(
                challenge=OuterRef('pk'),
                proposer=user
            )
            
            # 評価完了済みかどうかのサブクエリ
            has_completed_evals = UserEvaluationCompletion.objects.filter(
                challenge=OuterRef('pk'),
                user=user,
                has_completed_all_evaluations=True
            )
            
            # 提案者の並び順:
            # 1. 提案期間中で未提案
            # 2. 編集期間中（提案済み）
            # 3. 評価期間中で評価未完了（提案済み）
            # 4. 評価期間中で評価完了（提案済み）
            # 5. 期限切れ（提案済み or 未提案）
            # 同じ優先度内では期限が近い順
            queryset = queryset.annotate(
                user_has_proposed=Exists(has_proposed),
                user_has_completed_evaluations=Exists(has_completed_evals),
                priority_order=Case(
                    # 1. 提案期間中で未提案
                    When(
                        proposal_deadline__gte=now,
                        user_has_proposed=False,
                        then=Value(1)
                    ),
                    # 2. 編集期間中（提案済みのみ）
                    When(
                        proposal_deadline__lt=now,
                        edit_deadline__gte=now,
                        user_has_proposed=True,
                        then=Value(2)
                    ),
                    # 3. 評価期間中で評価未完了（提案済みのみ）
                    When(
                        edit_deadline__lt=now,
                        evaluation_deadline__gte=now,
                        user_has_proposed=True,
                        user_has_completed_evaluations=False,
                        then=Value(3)
                    ),
                    # 4. 評価期間中で評価完了（提案済みのみ）
                    When(
                        edit_deadline__lt=now,
                        evaluation_deadline__gte=now,
                        user_has_proposed=True,
                        user_has_completed_evaluations=True,
                        then=Value(4)
                    ),
                    # 5. 期限切れ or 未提案で提案期間過ぎた
                    default=Value(5),
                    output_field=IntegerField(),
                )
            ).order_by('priority_order', 'deadline')
            
            return queryset
        
        return Challenge.objects.none()
    
    def perform_create(self, serializer):
        """課題作成時の処理"""
        from .models import calculate_phase_deadlines
        user = self.request.user
        
        # 投稿者のみ作成可能
        if user.user_type != 'contributor':
            raise permissions.PermissionDenied("投稿者のみ課題を作成できます。")
        
        # 提案報酬を自動計算（バックエンドで計算式を隠蔽）
        validated_data = serializer.validated_data
        required_participants = validated_data['required_participants']
        
        # 選出可能な提案者数を再チェック（念のため）
        from selections.services import SelectionService
        temp_challenge = Challenge(contributor=user)
        eligible_users = SelectionService.get_eligible_users(temp_challenge)
        eligible_count = len(eligible_users)
        
        if required_participants > eligible_count:
            raise serializers.ValidationError(
                "申し訳ございませんが、現在登録されている提案者数が不足しています。より多くの提案者にご参加いただけるよう、引き続き努力してまいります。"
            )
        
        # 共通関数を使用して計算
        reward_amount_yen = calculate_reward_amount(required_participants)
        
        validated_data['reward_amount'] = reward_amount_yen
        
        # 採用報酬は万円単位の入力を円単位に変換
        validated_data['adoption_reward'] = validated_data['adoption_reward'] * 10000
        
        # 3つの期限を自動計算（最低6日必要）
        deadline = validated_data['deadline']
        created_at = timezone.now()
        total_delta = deadline - created_at
        
        if total_delta < timedelta(days=MIN_TOTAL_DAYS):
            raise serializers.ValidationError({
                'deadline': f'期限まで最低{MIN_TOTAL_DAYS}日必要です（提案3日、編集1日、評価2日以上）。'
            })
        total_days = math.ceil(total_delta.total_seconds() / 86400)
        if total_days > MAX_TOTAL_DAYS:
            raise serializers.ValidationError({
                'deadline': f'課題の総日数は最大{MAX_TOTAL_DAYS}日までです（作成日時から最終期限まで）。'
            })
        proposal_deadline, edit_deadline, evaluation_deadline = calculate_phase_deadlines(created_at, total_days)
        validated_data['proposal_deadline'] = proposal_deadline
        validated_data['edit_deadline'] = edit_deadline
        validated_data['evaluation_deadline'] = evaluation_deadline
        # 全体期限は評価期限に正規化して、フェーズ表示とのズレを防ぐ
        validated_data['deadline'] = evaluation_deadline
        
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
        from .models import calculate_phase_deadlines
        
        # 万円単位の入力を円単位に変換
        validated_data = serializer.validated_data
        if 'reward_amount' in validated_data:
            validated_data['reward_amount'] = validated_data['reward_amount'] * 10000
        if 'adoption_reward' in validated_data:
            validated_data['adoption_reward'] = validated_data['adoption_reward'] * 10000
        
        # 期限が変更された場合、3つの期限を再計算
        if 'deadline' in validated_data:
            challenge = self.get_object()
            deadline = validated_data['deadline']
            created_at = challenge.created_at
            total_delta = deadline - created_at
            
            if total_delta < timedelta(days=MIN_TOTAL_DAYS):
                raise serializers.ValidationError({
                    'deadline': f'期限まで最低{MIN_TOTAL_DAYS}日必要です（提案3日、編集1日、評価2日以上）。'
                })
            total_days = math.ceil(total_delta.total_seconds() / 86400)
            if total_days > MAX_TOTAL_DAYS:
                raise serializers.ValidationError({
                    'deadline': f'課題の総日数は最大{MAX_TOTAL_DAYS}日までです（作成日時から最終期限まで）。'
                })
            proposal_deadline, edit_deadline, evaluation_deadline = calculate_phase_deadlines(created_at, total_days)
            validated_data['proposal_deadline'] = proposal_deadline
            validated_data['edit_deadline'] = edit_deadline
            validated_data['evaluation_deadline'] = evaluation_deadline
            # 全体期限は評価期限に正規化して、フェーズ表示とのズレを防ぐ
            validated_data['deadline'] = evaluation_deadline
        
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
    
    if participants > MAX_SELECTION_PARTICIPANTS:
        return Response(
            {
                'error': (
                    f'選出人数は{MAX_SELECTION_PARTICIPANTS}人以下である必要があります。'
                )
            },
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


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def finalize_adoption(request, pk):
    """
    期限切れの課題で採用候補の集合を確定し、challenge.status を completed にする。
    proposal_ids で採用にする提案IDのみ true、それ以外は false に統一する。
    """
    challenge = get_object_or_404(Challenge, pk=pk)
    user = request.user
    if not getattr(user, 'user_type', None) == 'contributor':
        raise permissions.PermissionDenied('投稿者のみ採用を確定できます。')
    if challenge.contributor_id != getattr(user, 'id', None):
        raise permissions.PermissionDenied('自分の課題のみ確定できます。')

    if challenge.status == 'completed':
        return Response(
            {'detail': 'すでに採用を確定済みです。変更はできません。'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if challenge.get_current_phase() != 'closed':
        return Response(
            {'detail': '期限切れの課題でのみ採用を確定できます。'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    raw_ids = request.data.get('proposal_ids')
    if raw_ids is None:
        raw_ids = []
    if not isinstance(raw_ids, list):
        return Response(
            {'detail': 'proposal_ids はリストで指定してください。'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        id_set = {int(x) for x in raw_ids}
    except (TypeError, ValueError):
        return Response(
            {'detail': 'proposal_ids は整数のリストにしてください。'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    valid_ids = set(
        Proposal.objects.filter(challenge=challenge).values_list('id', flat=True)
    )
    if not id_set.issubset(valid_ids):
        return Response(
            {'detail': 'この課題に存在しない解決案IDが含まれています。'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    with transaction.atomic():
        for prop in Proposal.objects.filter(challenge=challenge).select_for_update():
            prop.is_adopted = prop.id in id_set
            prop.save(update_fields=['is_adopted'])
        challenge.status = 'completed'
        challenge.save(update_fields=['status', 'updated_at'])

    serializer = ChallengeSerializer(challenge, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)