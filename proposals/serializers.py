from rest_framework import serializers
from .models import Proposal, ProposalComment, ProposalEvaluation
from accounts.serializers import UserSerializer
from challenges.serializers import ChallengeSerializer

class ProposalSerializer(serializers.ModelSerializer):
    """
    提案シリアライザー
    提案の作成・更新・取得に使用
    """
    # 関連する提案者と課題の情報を表示用に含める
    proposer_info = UserSerializer(source='proposer', read_only=True)
    challenge_info = ChallengeSerializer(source='challenge', read_only=True)
    
    # 評価情報を追加
    evaluation_count = serializers.SerializerMethodField()
    evaluation_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = Proposal
        fields = [
            'id',
            'challenge',
            'challenge_info',
            'proposer',
            'proposer_info',
            'conclusion',
            'reasoning',
            'is_adopted',
            'is_deleted',
            'evaluation_count',
            'evaluation_summary',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'proposer', 'is_adopted', 'created_at', 'updated_at']
    
    def get_evaluation_count(self, obj):
        """評価数の取得"""
        return obj.evaluations.count()
    
    def get_evaluation_summary(self, obj):
        """評価サマリーの取得"""
        evaluations = obj.evaluations.all()
        if not evaluations.exists():
            return {'yes': 0, 'maybe': 0, 'no': 0}
        
        summary = {'yes': 0, 'maybe': 0, 'no': 0}
        for evaluation in evaluations:
            summary[evaluation.evaluation] += 1
        
        return summary
    
    def validate_challenge(self, value):
        """課題のバリデーション"""
        if value.status != 'open':
            raise serializers.ValidationError("募集中の課題のみ提案できます。")
        return value
    
    def validate_conclusion(self, value):
        """結論のバリデーション"""
        if not value.strip():
            raise serializers.ValidationError("結論は必須です。")
        return value.strip()
    
    def validate_reasoning(self, value):
        """理由のバリデーション"""
        if not value.strip():
            raise serializers.ValidationError("理由は必須です。")
        return value.strip()

class ProposalCreateSerializer(serializers.ModelSerializer):
    """
    提案作成専用シリアライザー
    提案者のみが使用可能
    """
    class Meta:
        model = Proposal
        fields = [
            'challenge',
            'conclusion',
            'reasoning'
        ]
    
    def validate_challenge(self, value):
        """課題のバリデーション"""
        if value.status != 'open':
            raise serializers.ValidationError("募集中の課題のみ提案できます。")
        return value
    
    def validate_conclusion(self, value):
        """結論のバリデーション"""
        if not value.strip():
            raise serializers.ValidationError("結論は必須です。")
        return value.strip()
    
    def validate_reasoning(self, value):
        """理由のバリデーション"""
        if not value.strip():
            raise serializers.ValidationError("理由は必須です。")
        return value.strip()

class ProposalListSerializer(serializers.ModelSerializer):
    """
    提案一覧表示用シリアライザー
    必要最小限の情報のみを含む
    """
    proposer_name = serializers.CharField(source='proposer.username', read_only=True)
    challenge_title = serializers.CharField(source='challenge.title', read_only=True)
    evaluation_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Proposal
        fields = [
            'id',
            'challenge',
            'challenge_title',
            'proposer_name',
            'conclusion',
            'is_adopted',
            'evaluation_count',
            'created_at'
        ]
    
    def get_evaluation_count(self, obj):
        """評価数の取得"""
        return obj.evaluations.count()

class ProposalCommentSerializer(serializers.ModelSerializer):
    """
    提案コメントシリアライザー
    コメントの作成・取得に使用
    """
    commenter_info = UserSerializer(source='commenter', read_only=True)
    
    class Meta:
        model = ProposalComment
        fields = [
            'id',
            'proposal',
            'commenter',
            'commenter_info',
            'target_section',
            'conclusion',
            'reasoning',
            'is_deleted',
            'created_at'
        ]
        read_only_fields = ['id', 'commenter', 'created_at']
    
    def validate_conclusion(self, value):
        """結論のバリデーション"""
        if not value.strip():
            raise serializers.ValidationError("コメントの結論は必須です。")
        return value.strip()
    
    def validate_reasoning(self, value):
        """理由のバリデーション"""
        if not value.strip():
            raise serializers.ValidationError("コメントの理由は必須です。")
        return value.strip()

class ProposalCommentCreateSerializer(serializers.ModelSerializer):
    """
    提案コメント作成専用シリアライザー
    """
    class Meta:
        model = ProposalComment
        fields = [
            'proposal',
            'target_section',
            'conclusion',
            'reasoning'
        ]
    
    def validate_conclusion(self, value):
        """結論のバリデーション"""
        if not value.strip():
            raise serializers.ValidationError("コメントの結論は必須です。")
        return value.strip()
    
    def validate_reasoning(self, value):
        """理由のバリデーション"""
        if not value.strip():
            raise serializers.ValidationError("コメントの理由は必須です。")
        return value.strip()

class ProposalEvaluationSerializer(serializers.ModelSerializer):
    """
    提案評価シリアライザー
    評価の作成・取得に使用
    """
    evaluator_info = UserSerializer(source='evaluator', read_only=True)
    evaluation_display = serializers.CharField(source='evaluation_display', read_only=True)
    
    class Meta:
        model = ProposalEvaluation
        fields = [
            'id',
            'proposal',
            'evaluator',
            'evaluator_info',
            'evaluation',
            'evaluation_display',
            'created_at'
        ]
        read_only_fields = ['id', 'evaluator', 'created_at']
    
    def validate_evaluation(self, value):
        """評価のバリデーション"""
        valid_choices = [choice[0] for choice in ProposalEvaluation.EVALUATION_CHOICES]
        if value not in valid_choices:
            raise serializers.ValidationError(f"評価は {', '.join(valid_choices)} のいずれかである必要があります。")
        return value

class ProposalEvaluationCreateSerializer(serializers.ModelSerializer):
    """
    提案評価作成専用シリアライザー
    """
    class Meta:
        model = ProposalEvaluation
        fields = [
            'proposal',
            'evaluation'
        ]
    
    def validate_evaluation(self, value):
        """評価のバリデーション"""
        valid_choices = [choice[0] for choice in ProposalEvaluation.EVALUATION_CHOICES]
        if value not in valid_choices:
            raise serializers.ValidationError(f"評価は {', '.join(valid_choices)} のいずれかである必要があります。")
        return value
