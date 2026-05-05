from rest_framework import serializers
from .models import Proposal, AnonymousName, ProposalComment, ProposalEvaluation, ProposalCommentReply, ProposalReference, ProposalEditReference
from accounts.serializers import UserSerializer
from challenges.serializers import ChallengeSerializer

class AnonymousNameSerializer(serializers.ModelSerializer):
    """匿名名シリアライザー"""
    class Meta:
        model = AnonymousName
        fields = ['id', 'name', 'category']


def challenge_participant_display_name(challenge, user):
    """
    課題内で選出された参加者の表示名（ChallengeUserAnonymousName → 無ければ当該課題の自分の提案の匿名名 → username）
    """
    if not user or not getattr(user, 'is_authenticated', False):
        return None
    from selections.models import ChallengeUserAnonymousName

    try:
        row = ChallengeUserAnonymousName.objects.select_related('anonymous_name').get(
            challenge=challenge, user=user
        )
        if row.anonymous_name_id:
            return row.anonymous_name.name
    except ChallengeUserAnonymousName.DoesNotExist:
        pass
    prop = (
        challenge.proposals.filter(proposer=user)
        .select_related('anonymous_name')
        .first()
    )
    if prop and prop.is_anonymous and prop.anonymous_name_id:
        return prop.anonymous_name.name
    return user.username


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

class ProposalUpdateSerializer(serializers.ModelSerializer):
    """
    提案更新用シリアライザー（参考コメントID受け取り対応）
    """
    reference_comment_id = serializers.IntegerField(required=False, allow_null=True, write_only=True)

    class Meta:
        model = Proposal
        fields = ['conclusion', 'reasoning', 'reference_comment_id']

    def update(self, instance, validated_data):
        reference_comment_id = validated_data.pop('reference_comment_id', None)
        if 'conclusion' in validated_data:
            instance.conclusion = validated_data['conclusion']
        if 'reasoning' in validated_data:
            instance.reasoning = validated_data['reasoning']
        instance.save()

        if reference_comment_id:
            try:
                comment = ProposalComment.objects.get(
                    id=reference_comment_id,
                    proposal=instance,
                    is_deleted=False
                )
                ProposalEditReference.objects.get_or_create(
                    proposal=instance,
                    comment=comment
                )
            except ProposalComment.DoesNotExist:
                pass
        return instance


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
    # ユーザー属性（全体満了後の解決案一覧用）
    nationality = serializers.SerializerMethodField()
    gender = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    challenge_current_phase = serializers.SerializerMethodField()
    challenge_status = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()
    challenge_updated_at = serializers.DateTimeField(source='challenge.updated_at', read_only=True)

    def get_challenge_current_phase(self, obj):
        return obj.challenge.get_current_phase()

    def get_challenge_status(self, obj):
        return obj.challenge.status

    def get_is_mine(self, obj):
        request = self.context.get('request')
        if not request or not getattr(request.user, 'is_authenticated', False):
            return False
        return obj.proposer_id == request.user.id

    def get_proposer_name(self, obj):
        """リクエストユーザーを考慮した表示名を返す"""
        request = self.context.get('request')
        request_user = None
        if request and hasattr(request, 'user'):
            request_user = request.user
        return obj.get_display_name(request_user)
    
    def get_nationality(self, obj):
        """提案者の国籍を返す（全体期限経過済みかつ選出ユーザーの場合のみ）"""
        challenge = obj.challenge
        
        # 募集期限（deadline）が経過済みか
        from django.utils import timezone
        if challenge.deadline >= timezone.now():
            return None
        
        # 提案者が選出されているかを確認
        from selections.models import Selection
        is_selected = Selection.objects.filter(
            challenge=challenge,
            selected_users=obj.proposer
        ).exists()
        
        if is_selected:
            # ProposerProfileから国籍を取得
            try:
                return obj.proposer.proposer_profile.nationality
            except:
                return None
        return None
    
    def get_gender(self, obj):
        """提案者の性別を返す（全体期限経過済みかつ選出ユーザーの場合のみ）"""
        challenge = obj.challenge
        
        # 募集期限（deadline）が経過済みか
        from django.utils import timezone
        if challenge.deadline >= timezone.now():
            return None
        
        # 提案者が選出されているかを確認
        from selections.models import Selection
        is_selected = Selection.objects.filter(
            challenge=challenge,
            selected_users=obj.proposer
        ).exists()
        
        if is_selected:
            # ProposerProfileから性別を取得
            try:
                return obj.proposer.proposer_profile.gender
            except:
                return None
        return None
    
    def get_age(self, obj):
        """提案者の年齢を返す（全体期限経過済みかつ選出ユーザーの場合のみ）"""
        challenge = obj.challenge
        
        # 募集期限（deadline）が経過済みか
        from django.utils import timezone
        if challenge.deadline >= timezone.now():
            return None
        
        # 提案者が選出されているかを確認
        from selections.models import Selection
        is_selected = Selection.objects.filter(
            challenge=challenge,
            selected_users=obj.proposer
        ).exists()
        
        if is_selected:
            # ProposerProfileから年齢を計算
            try:
                from datetime import date
                birth_date = obj.proposer.proposer_profile.birth_date
                today = date.today()
                age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                return age
            except:
                return None
        return None
    
    def get_unread_comment_count(self, obj):
        """未読コメント数を返す"""
        request = self.context.get('request')
        request_user = None
        if request and hasattr(request, 'user'):
            request_user = request.user
        
        # 自分の提案の未読コメント数を返す
        if request_user and obj.proposer == request_user:
            return obj.comments.filter(is_read=False, is_deleted=False).count()
        return 0
    
    def get_total_comment_count(self, obj):
        """総コメント数を返す"""
        count = obj.comments.filter(is_deleted=False).count()
        return count
    
    class Meta:
        model = Proposal
        fields = [
            'id', 'conclusion', 'reasoning',
            'challenge_id', 'challenge_title', 'proposer_name',
            'anonymous_name_info', 'is_anonymous', 'status', 'is_adopted',
            'rating', 'rating_count', 'created_at', 'updated_at', 'unread_comment_count', 'total_comment_count',
            'nationality', 'gender', 'age',
            'challenge_current_phase', 'challenge_status', 'challenge_updated_at', 'is_mine',
        ]


class ProposalCommentReplySerializer(serializers.ModelSerializer):
    """コメント返信シリアライザー"""
    replier_name = serializers.SerializerMethodField()
    replier = serializers.IntegerField(source='replier_id', read_only=True)

    def get_replier_name(self, obj):
        """返信者の表示名を返す（課題ごとの匿名名）"""
        challenge = obj.comment.proposal.challenge
        return challenge_participant_display_name(challenge, obj.replier)

    class Meta:
        model = ProposalCommentReply
        fields = ['id', 'content', 'replier', 'replier_name', 'created_at']
        read_only_fields = ['id', 'replier', 'replier_name', 'created_at']


class ProposalCommentSerializer(serializers.ModelSerializer):
    """提案コメントシリアライザー"""
    commenter_name = serializers.SerializerMethodField()
    commenter = serializers.IntegerField(source='commenter_id', read_only=True)
    replies = ProposalCommentReplySerializer(many=True, read_only=True)

    def get_commenter_name(self, obj):
        """コメント投稿者の表示名を返す（課題ごとの匿名名）"""
        challenge = obj.proposal.challenge
        return challenge_participant_display_name(challenge, obj.commenter)

    class Meta:
        model = ProposalComment
        fields = [
            'id', 'commenter', 'target_section', 'conclusion', 'reasoning',
            'commenter_name', 'created_at', 'replies'
        ]
        read_only_fields = ['id', 'commenter', 'created_at']


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
        fields = ['id', 'proposal', 'evaluator', 'evaluation', 'score', 'insight_level', 'insight_score', 'evaluator_name', 'created_at', 'updated_at']
        read_only_fields = ['id', 'proposal', 'evaluator', 'score', 'insight_score', 'evaluator_name', 'created_at', 'updated_at']
    
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