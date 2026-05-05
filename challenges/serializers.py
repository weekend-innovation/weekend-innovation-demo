import math

from rest_framework import serializers
from mvp_project.limits import MAX_SELECTION_PARTICIPANTS

from .models import Challenge
from accounts.serializers import UserSerializer

class ChallengeSerializer(serializers.ModelSerializer):
    """
    課題シリアライザー
    課題の作成・更新・取得に使用
    """
    # 関連する投稿者の情報を表示用に含める
    contributor_info = serializers.SerializerMethodField()
    contributor_name = serializers.SerializerMethodField()
    # 現在のフェーズ情報
    current_phase = serializers.CharField(source='get_current_phase', read_only=True)
    phase_display = serializers.CharField(read_only=True)
    has_completed_all_evaluations = serializers.SerializerMethodField()
    
    class Meta:
        model = Challenge
        fields = [
            'id',
            'title',
            'description',
            'contributor',
            'contributor_info',
            'contributor_name',
            'is_contributor_anonymous',
            'reward_amount',
            'adoption_reward',
            'required_participants',
            'deadline',
            'proposal_deadline',
            'edit_deadline',
            'evaluation_deadline',
            'current_phase',
            'phase_display',
            'status',
            'created_at',
            'updated_at',
            'has_completed_all_evaluations'
        ]
        read_only_fields = ['id', 'contributor', 'created_at', 'updated_at', 'proposal_deadline', 'edit_deadline', 'evaluation_deadline']

    def _can_view_real_contributor(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return request.user.id == obj.contributor_id

    def get_contributor_name(self, obj):
        if obj.is_contributor_anonymous and not self._can_view_real_contributor(obj):
            return '匿名'
        return obj.contributor.username

    def get_contributor_info(self, obj):
        data = UserSerializer(obj.contributor).data
        if obj.is_contributor_anonymous and not self._can_view_real_contributor(obj):
            data['username'] = '匿名'
            data['email'] = ''
        return data
    
    def get_has_completed_all_evaluations(self, obj):
        """
        現在のユーザーがこの課題の全ての解決案を評価したかどうか
        """
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        from selections.models import UserEvaluationCompletion
        try:
            completion = UserEvaluationCompletion.objects.get(
                challenge=obj,
                user=request.user
            )
            return completion.has_completed_all_evaluations
        except UserEvaluationCompletion.DoesNotExist:
            return False
    
    def validate_required_participants(self, value):
        """選出人数のバリデーション"""
        if value < 50:
            raise serializers.ValidationError("選出人数は50人以上にする必要があります。")
        if value > MAX_SELECTION_PARTICIPANTS:
            raise serializers.ValidationError(
                f"選出人数は{MAX_SELECTION_PARTICIPANTS}人以下にする必要があります。"
            )
        return value
    
    def validate_reward_amount(self, value):
        """提案報酬のバリデーション"""
        if value <= 0:
            raise serializers.ValidationError("提案報酬は0円より大きい必要があります。")
        return value
    
    def validate_adoption_reward(self, value):
        """採用報酬のバリデーション"""
        if value <= 0:
            raise serializers.ValidationError("採用報酬は0円より大きい必要があります。")
        return value
    
    def validate_deadline(self, value):
        """期限のバリデーション（最低6日・最大90日: カレンダー日数は作成日時基準で切り上げ）"""
        from datetime import timedelta
        from django.utils import timezone
        from challenges.models import MAX_TOTAL_DAYS, MIN_TOTAL_DAYS
        now = timezone.now()
        if value <= now:
            raise serializers.ValidationError("期限は現在時刻より後の日時である必要があります。")
        # 更新時はcreated_at、新規時はnowを基準
        start = self.instance.created_at if self.instance else now
        if (value - start) < timedelta(days=MIN_TOTAL_DAYS):
            raise serializers.ValidationError(
                f"期限まで最低{MIN_TOTAL_DAYS}日必要です（提案3日、編集1日、評価2日以上）。"
            )
        span_days = math.ceil((value - start).total_seconds() / 86400.0)
        if span_days > MAX_TOTAL_DAYS:
            raise serializers.ValidationError(
                f"課題の総日数は最大{MAX_TOTAL_DAYS}日までです（作成日時から最終期限まで）。"
            )
        return value

class ChallengeCreateSerializer(serializers.ModelSerializer):
    """
    課題作成専用シリアライザー
    投稿者のみが使用可能
    """
    # 関連する投稿者の情報を表示用に含める
    contributor_info = UserSerializer(source='contributor', read_only=True)
    
    class Meta:
        model = Challenge
        fields = [
            'id',
            'title',
            'description',
            'contributor',
            'contributor_info',
            'is_contributor_anonymous',
            'reward_amount',
            'adoption_reward',
            'required_participants',
            'deadline',
            'status',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'contributor', 'status', 'created_at', 'updated_at', 'reward_amount']
    
    def validate_required_participants(self, value):
        """選出人数のバリデーション"""
        from selections.services import SelectionService
        from challenges.models import Challenge
        
        if value < 50:
            raise serializers.ValidationError("選出人数は50人以上にする必要があります。")
        if value > MAX_SELECTION_PARTICIPANTS:
            raise serializers.ValidationError(
                f"選出人数は{MAX_SELECTION_PARTICIPANTS}人以下にする必要があります。"
            )
        
        # 選出可能な提案者数をチェック
        request = self.context.get('request')
        if request and request.user and request.user.user_type == 'contributor':
            try:
                # 一時的なChallengeオブジェクトを作成（保存はしない）
                temp_challenge = Challenge(contributor=request.user)
                eligible_users = SelectionService.get_eligible_users(temp_challenge)
                eligible_count = len(eligible_users)
                
                if value > eligible_count:
                    raise serializers.ValidationError(
                        "申し訳ございませんが、現在登録されている提案者数が不足しています。より多くの提案者にご参加いただけるよう、引き続き努力してまいります。"
                    )
            except serializers.ValidationError:
                # バリデーションエラーはそのまま再発生
                raise
            except Exception:
                # その他のエラーは無視（課題作成時に再度チェックされる）
                pass
        
        return value
    
    def validate_reward_amount(self, value):
        """提案報酬のバリデーション"""
        if value <= 0:
            raise serializers.ValidationError("提案報酬は0円より大きい必要があります。")
        return value
    
    def validate_adoption_reward(self, value):
        """採用報酬のバリデーション"""
        if value <= 0:
            raise serializers.ValidationError("採用報酬は0円より大きい必要があります。")
        return value
    
    def validate_deadline(self, value):
        """期限のバリデーション（最低6日・最大90日: カレンダー日数は現在時刻基準で切り上げ）"""
        from datetime import timedelta
        from django.utils import timezone
        from challenges.models import MAX_TOTAL_DAYS, MIN_TOTAL_DAYS
        now = timezone.now()
        if value <= now:
            raise serializers.ValidationError("期限は現在時刻より後の日時である必要があります。")
        if (value - now) < timedelta(days=MIN_TOTAL_DAYS):
            raise serializers.ValidationError(
                f"期限まで最低{MIN_TOTAL_DAYS}日必要です（提案3日、編集1日、評価2日以上）。"
            )
        span_days = math.ceil((value - now).total_seconds() / 86400.0)
        if span_days > MAX_TOTAL_DAYS:
            raise serializers.ValidationError(
                f"課題の総日数は最大{MAX_TOTAL_DAYS}日までです（現在から最終期限まで）。"
            )
        return value

class ChallengeListSerializer(serializers.ModelSerializer):
    """
    課題一覧表示用シリアライザー
    必要最小限の情報のみを含む
    """
    contributor_name = serializers.SerializerMethodField()
    current_phase = serializers.CharField(source='get_current_phase', read_only=True)
    phase_display = serializers.CharField(read_only=True)
    has_completed_all_evaluations = serializers.SerializerMethodField()
    has_proposed = serializers.SerializerMethodField()
    priority = serializers.SerializerMethodField()
    
    class Meta:
        model = Challenge
        fields = [
            'id',
            'title',
            'contributor_name',
            'is_contributor_anonymous',
            'reward_amount',
            'adoption_reward',
            'required_participants',
            'deadline',
            'proposal_deadline',
            'edit_deadline',
            'evaluation_deadline',
            'current_phase',
            'phase_display',
            'status',
            'created_at',
            'has_completed_all_evaluations',
            'has_proposed',
            'priority'
        ]

    def get_contributor_name(self, obj):
        request = self.context.get('request')
        if obj.is_contributor_anonymous and (
            not request or
            not request.user.is_authenticated or
            request.user.id != obj.contributor_id
        ):
            return '匿名'
        return obj.contributor.username
    
    def get_has_completed_all_evaluations(self, obj):
        """
        現在のユーザーがこの課題の全ての解決案を評価したかどうか
        """
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        from selections.models import UserEvaluationCompletion
        try:
            completion = UserEvaluationCompletion.objects.get(
                challenge=obj,
                user=request.user
            )
            return completion.has_completed_all_evaluations
        except UserEvaluationCompletion.DoesNotExist:
            return False
    
    def get_has_proposed(self, obj):
        """
        現在のユーザーがこの課題に提案しているかどうか
        """
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        return obj.has_user_proposed(request.user)
    
    def get_priority(self, obj):
        """
        現在のユーザーにとっての優先度
        """
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 999
        
        user = request.user
        
        if user.user_type == 'proposer':
            return obj.get_priority_for_proposer(user)
        else:
            # 投稿者の場合は現在のフェーズで優先度を決定
            phase = obj.get_current_phase()
            if phase == 'closed':
                return 5  # closed／満了は低優先度
            else:
                return 1  # アクティブな課題は高優先度