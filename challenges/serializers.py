from rest_framework import serializers
from .models import Challenge
from accounts.serializers import UserSerializer

class ChallengeSerializer(serializers.ModelSerializer):
    """
    課題シリアライザー
    課題の作成・更新・取得に使用
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
            'reward_amount',
            'adoption_reward',
            'required_participants',
            'deadline',
            'status',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'contributor', 'created_at', 'updated_at']
    
    def validate_required_participants(self, value):
        """選出人数のバリデーション"""
        if value <= 0:
            raise serializers.ValidationError("選出人数は1人以上である必要があります。")
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
        """期限のバリデーション"""
        from django.utils import timezone
        if value <= timezone.now():
            raise serializers.ValidationError("期限は現在時刻より後の日時である必要があります。")
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
            'reward_amount',
            'adoption_reward',
            'required_participants',
            'deadline',
            'status',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'contributor', 'status', 'created_at', 'updated_at']
    
    def validate_required_participants(self, value):
        """選出人数のバリデーション"""
        if value <= 0:
            raise serializers.ValidationError("選出人数は1人以上である必要があります。")
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
        """期限のバリデーション"""
        from django.utils import timezone
        if value <= timezone.now():
            raise serializers.ValidationError("期限は現在時刻より後の日時である必要があります。")
        return value

class ChallengeListSerializer(serializers.ModelSerializer):
    """
    課題一覧表示用シリアライザー
    必要最小限の情報のみを含む
    """
    contributor_name = serializers.CharField(source='contributor.username', read_only=True)
    
    class Meta:
        model = Challenge
        fields = [
            'id',
            'title',
            'contributor_name',
            'reward_amount',
            'adoption_reward',
            'required_participants',
            'deadline',
            'status',
            'created_at'
        ]
