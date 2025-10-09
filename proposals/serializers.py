from rest_framework import serializers
from .models import Proposal, AnonymousName, ProposalComment, ProposalEvaluation, ProposalCommentReply, ProposalReference
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
    unread_comment_count = serializers.SerializerMethodField()
    total_comment_count = serializers.SerializerMethodField()
    
    def get_proposer_name(self, obj):
        """リクエストユーザーを考慮した表示名を返す"""
        request = self.context.get('request')
        request_user = request.user if request else None
        return obj.get_display_name(request_user)
    
    def get_unread_comment_count(self, obj):
        """未読コメント数を返す"""
        request = self.context.get('request')
        request_user = request.user if request else None
        
        # 自分の提案の未読コメント数を返す
        if request_user and obj.proposer == request_user:
            return obj.comments.filter(is_read=False, is_deleted=False).count()
        return 0
    
    def get_total_comment_count(self, obj):
        """総コメント数を返す"""
        count = obj.comments.filter(is_deleted=False).count()
        print(f"DEBUG: Proposal {obj.id} total_comment_count: {count}")
        return count
    
    class Meta:
        model = Proposal
        fields = [
            'id', 'conclusion', 'reasoning',
            'challenge_id', 'challenge_title', 'proposer_name',
            'anonymous_name_info', 'is_anonymous', 'status', 'is_adopted',
            'rating', 'rating_count', 'created_at', 'updated_at', 'unread_comment_count', 'total_comment_count'
        ]


class ProposalCommentReplySerializer(serializers.ModelSerializer):
    """コメント返信シリアライザー"""
    replier_name = serializers.SerializerMethodField()
    
    def get_replier_name(self, obj):
        """返信者の表示名を返す（課題ごとの匿名名）"""
        from selections.models import ChallengeUserAnonymousName
        
        try:
            # 課題ごとの返信者の匿名名を取得
            challenge = obj.comment.proposal.challenge
            challenge_user_name = ChallengeUserAnonymousName.objects.select_related('anonymous_name').get(
                challenge=challenge,
                user=obj.replier
            )
            
            if challenge_user_name.anonymous_name:
                return challenge_user_name.anonymous_name.name
            else:
                return obj.replier.username
                
        except ChallengeUserAnonymousName.DoesNotExist:
            # 匿名名が割り当てられていない場合はusernameを返す
            return obj.replier.username
    
    class Meta:
        model = ProposalCommentReply
        fields = ['id', 'content', 'replier_name', 'created_at']
        read_only_fields = ['id', 'replier_name', 'created_at']


class ProposalCommentSerializer(serializers.ModelSerializer):
    """提案コメントシリアライザー"""
    commenter_name = serializers.SerializerMethodField()
    replies = ProposalCommentReplySerializer(many=True, read_only=True)
    
    def get_commenter_name(self, obj):
        """コメント投稿者の表示名を返す（課題ごとの匿名名）"""
        from selections.models import ChallengeUserAnonymousName
        
        try:
            # 課題ごとのコメント投稿者の匿名名を取得
            challenge = obj.proposal.challenge
            challenge_user_name = ChallengeUserAnonymousName.objects.select_related('anonymous_name').get(
                challenge=challenge,
                user=obj.commenter
            )
            
            if challenge_user_name.anonymous_name:
                return challenge_user_name.anonymous_name.name
            else:
                return obj.commenter.username
                
        except ChallengeUserAnonymousName.DoesNotExist:
            # 匿名名が割り当てられていない場合はusernameを返す
            return obj.commenter.username
    
    class Meta:
        model = ProposalComment
        fields = [
            'id', 'target_section', 'conclusion', 'reasoning',
            'commenter_name', 'created_at', 'replies'
        ]
        read_only_fields = ['id', 'created_at']


class ProposalCommentCreateSerializer(serializers.ModelSerializer):
    """提案コメント作成用シリアライザー"""
    class Meta:
        model = ProposalComment
        fields = ['target_section', 'conclusion', 'reasoning']
    
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


class ProposalEvaluationSerializer(serializers.ModelSerializer):
    """提案評価シリアライザー"""
    evaluator_name = serializers.CharField(source='evaluator.username', read_only=True)
    
    class Meta:
        model = ProposalEvaluation
        fields = ['id', 'proposal', 'evaluator', 'evaluation', 'score', 'evaluator_name', 'created_at']
        read_only_fields = ['id', 'proposal', 'evaluator', 'score', 'evaluator_name', 'created_at']
    
    def create(self, validated_data):
        """評価作成時の処理（スコアはモデルのsaveメソッドで自動計算）"""
        # スコアはモデルのsaveメソッドで自動計算されるため、ここでは設定しない
        return super().create(validated_data)


class ProposalReferenceSerializer(serializers.ModelSerializer):
    """提案参考シリアライザー"""
    referencer_name = serializers.CharField(source='referencer.username', read_only=True)
    
    class Meta:
        model = ProposalReference
        fields = ['id', 'notes', 'referencer_name', 'created_at']
        read_only_fields = ['id', 'referencer_name', 'created_at']


class ProposalDetailSerializer(ProposalSerializer):
    """提案詳細シリアライザー（コメント・評価情報を含む）"""
    comments = ProposalCommentSerializer(many=True, read_only=True)
    evaluations = ProposalEvaluationSerializer(many=True, read_only=True)
    user_evaluation = serializers.SerializerMethodField()
    user_reference = serializers.SerializerMethodField()
    
    def get_user_evaluation(self, obj):
        """現在のユーザーの評価を取得"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                evaluation = obj.evaluations.get(evaluator=request.user)
                return ProposalEvaluationSerializer(evaluation).data
            except ProposalEvaluation.DoesNotExist:
                return None
        return None
    
    def get_user_reference(self, obj):
        """現在のユーザーの参考登録を取得"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                reference = obj.references.get(referencer=request.user)
                return ProposalReferenceSerializer(reference).data
            except ProposalReference.DoesNotExist:
                return None
        return None
    
    class Meta(ProposalSerializer.Meta):
        fields = ProposalSerializer.Meta.fields + [
            'comments', 'evaluations', 'user_evaluation', 'user_reference'
        ]