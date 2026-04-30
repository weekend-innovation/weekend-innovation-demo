"""
選出機能のシリアライザー
API用のデータ変換を提供
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Selection, SelectionHistory, SelectionCriteria
from challenges.serializers import ChallengeSerializer
from accounts.serializers import UserSerializer

User = get_user_model()


class SelectionCriteriaSerializer(serializers.ModelSerializer):
    """
    選出基準のシリアライザー
    """
    
    class Meta:
        model = SelectionCriteria
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class SelectionHistorySerializer(serializers.ModelSerializer):
    """
    選出履歴のシリアライザー
    """
    user = UserSerializer(read_only=True)
    user_username = serializers.ReadOnlyField(source='user.username')
    
    class Meta:
        model = SelectionHistory
        fields = '__all__'
        read_only_fields = ('created_at',)


class SelectionSerializer(serializers.ModelSerializer):
    """
    選出のシリアライザー
    """
    challenge = ChallengeSerializer(read_only=True)
    contributor = UserSerializer(read_only=True)
    selected_users = UserSerializer(many=True, read_only=True)
    contributor_username = serializers.ReadOnlyField(source='contributor.username')
    challenge_title = serializers.ReadOnlyField(source='challenge.title')
    is_completed = serializers.ReadOnlyField()
    remaining_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Selection
        fields = '__all__'
        read_only_fields = ('contributor', 'selected_count', 'created_at', 'updated_at', 'completed_at')
    
    def validate_required_count(self, value):
        """選出人数のバリデーション"""
        if value <= 0:
            raise serializers.ValidationError("選出人数は1以上である必要があります")
        if value > 300:
            raise serializers.ValidationError("選出人数は300人以下である必要があります。匿名化用の名前数の上限に達しています。")
        return value
    
    def validate(self, data):
        """全体的なバリデーション"""
        challenge = data.get('challenge')
        if challenge and challenge.contributor != self.context['request'].user:
            raise serializers.ValidationError("自分の課題のみ選出を作成できます")
        return data


class SelectionCreateSerializer(serializers.ModelSerializer):
    """
    選出作成用のシリアライザー
    """
    challenge_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Selection
        fields = [
            'challenge_id', 'required_count', 'selection_method', 
            'selection_criteria'
        ]
    
    def validate_challenge_id(self, value):
        """課題IDのバリデーション"""
        try:
            from challenges.models import Challenge
            challenge = Challenge.objects.get(id=value)
            if challenge.contributor != self.context['request'].user:
                raise serializers.ValidationError("自分の課題のみ選出を作成できます")
            if challenge.status != 'open':
                raise serializers.ValidationError("募集中の課題のみ選出できます")
            return value
        except Challenge.DoesNotExist:
            raise serializers.ValidationError("課題が見つかりません")
    
    def create(self, validated_data):
        """選出オブジェクトの作成"""
        challenge_id = validated_data.pop('challenge_id')
        from challenges.models import Challenge
        challenge = Challenge.objects.get(id=challenge_id)
        
        validated_data.update({
            'challenge': challenge,
            'contributor': self.context['request'].user,
        })
        
        return super().create(validated_data)


class SelectionUpdateSerializer(serializers.ModelSerializer):
    """
    選出更新用のシリアライザー
    """
    
    class Meta:
        model = Selection
        fields = ['status', 'selection_criteria']
    
    def validate_status(self, value):
        """ステータスのバリデーション"""
        if value not in ['pending', 'completed', 'cancelled']:
            raise serializers.ValidationError("無効なステータスです")
        return value


class SelectionListSerializer(serializers.ModelSerializer):
    """
    選出一覧用のシリアライザー
    """
    challenge_title = serializers.ReadOnlyField(source='challenge.title')
    contributor_username = serializers.ReadOnlyField(source='contributor.username')
    selected_users_count = serializers.SerializerMethodField()
    is_completed = serializers.ReadOnlyField()
    
    class Meta:
        model = Selection
        fields = [
            'id', 'challenge', 'challenge_title', 'contributor', 'contributor_username',
            'required_count', 'selected_count', 'selected_users_count', 'status',
            'selection_method', 'notification_sent', 'is_completed',
            'created_at', 'completed_at'
        ]
    
    def get_selected_users_count(self, obj):
        """選出されたユーザー数を取得"""
        return obj.selected_users.count()


class SelectionDetailSerializer(SelectionSerializer):
    """
    選出詳細用のシリアライザー
    """
    history = SelectionHistorySerializer(many=True, read_only=True)
    selected_users_list = serializers.SerializerMethodField()
    
    class Meta:
        model = Selection
        fields = '__all__'
    
    def get_selected_users_list(self, obj):
        """選出されたユーザーの詳細リストを取得"""
        return [
            {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': getattr(user.proposer_profile, 'full_name', '') if hasattr(user, 'proposer_profile') else '',
                'expertise': getattr(user.proposer_profile, 'expertise', '') if hasattr(user, 'proposer_profile') else '',
            }
            for user in obj.selected_users.all()
        ]


class SelectionStatisticsSerializer(serializers.Serializer):
    """
    選出統計のシリアライザー
    """
    total_selections = serializers.IntegerField()
    completed_selections = serializers.IntegerField()
    pending_selections = serializers.IntegerField()
    cancelled_selections = serializers.IntegerField()
    total_selected_users = serializers.IntegerField()
    average_selection_size = serializers.FloatField()
    completion_rate = serializers.FloatField()


class SelectionRequestSerializer(serializers.Serializer):
    """
    選出リクエスト用のシリアライザー
    """
    challenge_id = serializers.IntegerField()
    required_count = serializers.IntegerField(min_value=1, max_value=300)
    selection_method = serializers.ChoiceField(
        choices=['random', 'weighted'],
        default='random'
    )
    selection_criteria = serializers.JSONField(default=dict, required=False)
    
    def validate_challenge_id(self, value):
        """課題IDのバリデーション"""
        try:
            from challenges.models import Challenge
            challenge = Challenge.objects.get(id=value)
            if challenge.contributor != self.context['request'].user:
                raise serializers.ValidationError("自分の課題のみ選出できます")
            if challenge.status != 'open':
                raise serializers.ValidationError("募集中の課題のみ選出できます")
            return value
        except Challenge.DoesNotExist:
            raise serializers.ValidationError("課題が見つかりません")

