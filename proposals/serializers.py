from rest_framework import serializers
from .models import Proposal, AnonymousName
from accounts.serializers import UserSerializer
from challenges.serializers import ChallengeSerializer

class AnonymousNameSerializer(serializers.ModelSerializer):
    """匿名名シリアライザー"""
    class Meta:
        model = AnonymousName
        fields = ['id', 'name', 'category']

class ProposalSerializer(serializers.ModelSerializer):
    """
    提案シリアライザー
    提案の作成・更新・取得に使用
    """
    # 関連する提案者と課題の情報を表示用に含める
    proposer_info = UserSerializer(source='proposer', read_only=True)
    challenge_info = ChallengeSerializer(source='challenge', read_only=True)
    anonymous_name_info = AnonymousNameSerializer(source='anonymous_name', read_only=True)
    
    # 表示名を追加
    display_name = serializers.SerializerMethodField()
    
    def get_display_name(self, obj):
        """リクエストユーザーを考慮した表示名を返す"""
        request = self.context.get('request')
        request_user = request.user if request else None
        return obj.get_display_name(request_user)
    
    class Meta:
        model = Proposal
        fields = [
            'id', 'conclusion', 'reasoning',
            'challenge', 'proposer', 'anonymous_name',
            'is_anonymous', 'status', 'is_adopted',
            'rating', 'rating_count',
            'created_at', 'updated_at',
            'proposer_info', 'challenge_info', 'anonymous_name_info',
            'display_name'
        ]
        read_only_fields = [
            'id', 'proposer', 'anonymous_name', 'is_anonymous',
            'rating', 'rating_count', 'created_at', 'updated_at'
        ]

class ProposalCreateSerializer(serializers.ModelSerializer):
    """
    提案作成用シリアライザー
    提案作成時に使用
    """
    class Meta:
        model = Proposal
        fields = [
            'conclusion', 'reasoning', 'challenge'
        ]
    
    def validate_conclusion(self, value):
        """結論のバリデーション"""
        if len(value.strip()) < 10:
            raise serializers.ValidationError("結論は10文字以上で入力してください。")
        return value.strip()
    
    def validate_reasoning(self, value):
        """理由のバリデーション"""
        if len(value.strip()) < 20:
            raise serializers.ValidationError("理由は20文字以上で入力してください。")
        return value.strip()

class ProposalListSerializer(serializers.ModelSerializer):
    """
    提案一覧表示用シリアライザー
    一覧表示時に使用
    """
    proposer_name = serializers.SerializerMethodField()
    challenge_title = serializers.CharField(source='challenge.title', read_only=True)
    challenge_id = serializers.IntegerField(source='challenge.id', read_only=True)
    anonymous_name_info = AnonymousNameSerializer(source='anonymous_name', read_only=True)
    
    def get_proposer_name(self, obj):
        """リクエストユーザーを考慮した表示名を返す"""
        request = self.context.get('request')
        request_user = request.user if request else None
        return obj.get_display_name(request_user)
    
    class Meta:
        model = Proposal
        fields = [
            'id', 'conclusion', 'reasoning',
            'challenge_id', 'challenge_title', 'proposer_name',
            'anonymous_name_info', 'is_anonymous', 'status', 'is_adopted',
            'rating', 'rating_count', 'created_at', 'updated_at'
        ]