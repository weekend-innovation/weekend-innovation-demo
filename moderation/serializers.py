"""
モデレーション管理のシリアライザー
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from .models import Report, UserSuspension, ModerationAction

User = get_user_model()


class ReportSerializer(serializers.ModelSerializer):
    """報告シリアライザー"""
    
    reporter_username = serializers.CharField(source='reporter.username', read_only=True)
    content_type_name = serializers.CharField(source='get_content_type_name', read_only=True)
    moderator_username = serializers.CharField(source='moderator.username', read_only=True)
    
    class Meta:
        model = Report
        fields = [
            'id',
            'reporter',
            'reporter_username',
            'content_type',
            'object_id',
            # 'content_object',  # JSONシリアライズエラーを防ぐため除外
            'content_type_name',
            'reason',
            'description',
            'status',
            'moderator',
            'moderator_username',
            'moderator_notes',
            'created_at',
            'updated_at',
            'resolved_at',
        ]
        read_only_fields = [
            'id',
            'reporter',
            'reporter_username',
            'content_type_name',
            'moderator_username',
            'created_at',
            'updated_at',
            'resolved_at',
        ]


class ReportCreateSerializer(serializers.ModelSerializer):
    """報告作成用シリアライザー"""
    
    # content_typeはPrimaryKeyRelatedFieldとして明示的に定義
    content_type = serializers.PrimaryKeyRelatedField(
        queryset=ContentType.objects.all()
    )
    
    class Meta:
        model = Report
        fields = [
            'content_type',
            'object_id',
            'reason',
            'description',
        ]
    
    def validate(self, data):
        """バリデーション"""
        content_type = data.get('content_type')
        object_id = data.get('object_id')
        
        # コンテンツオブジェクトの存在確認
        try:
            model_class = content_type.model_class()
            if not model_class.objects.filter(id=object_id).exists():
                raise serializers.ValidationError("指定されたコンテンツが存在しません。")
        except Exception as e:
            raise serializers.ValidationError(f"無効なコンテンツタイプです。エラー: {str(e)}")
        
        return data


class ReportUpdateSerializer(serializers.ModelSerializer):
    """報告更新用シリアライザー（モデレーター用）"""
    
    class Meta:
        model = Report
        fields = [
            'status',
            'moderator_notes',
        ]
    
    def update(self, instance, validated_data):
        """更新処理"""
        from django.utils import timezone
        
        # ステータスが解決済みに変更された場合、解決日時を設定
        if validated_data.get('status') == 'resolved' and instance.status != 'resolved':
            validated_data['resolved_at'] = timezone.now()
        
        return super().update(instance, validated_data)


class UserSuspensionSerializer(serializers.ModelSerializer):
    """ユーザー利用停止シリアライザー"""
    
    user_username = serializers.CharField(source='user.username', read_only=True)
    moderator_username = serializers.CharField(source='moderator.username', read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    days_remaining = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = UserSuspension
        fields = [
            'id',
            'user',
            'user_username',
            'reason',
            'description',
            'suspended_from',
            'suspended_until',
            'status',
            'moderator',
            'moderator_username',
            'related_reports',
            'is_active',
            'days_remaining',
            'created_at',
            'updated_at',
            'lifted_at',
        ]
        read_only_fields = [
            'id',
            'user_username',
            'moderator_username',
            'is_active',
            'days_remaining',
            'created_at',
            'updated_at',
            'lifted_at',
        ]


class UserSuspensionCreateSerializer(serializers.ModelSerializer):
    """ユーザー利用停止作成用シリアライザー"""
    
    class Meta:
        model = UserSuspension
        fields = [
            'user',
            'reason',
            'description',
            'suspended_until',
            'related_reports',
        ]
    
    def validate_suspended_until(self, value):
        """停止終了日時のバリデーション"""
        from django.utils import timezone
        
        if value <= timezone.now():
            raise serializers.ValidationError("停止終了日時は現在時刻より後の日時を指定してください。")
        
        return value


class ModerationActionSerializer(serializers.ModelSerializer):
    """モデレーションアクション履歴シリアライザー"""
    
    moderator_username = serializers.CharField(source='moderator.username', read_only=True)
    target_user_username = serializers.CharField(source='target_user.username', read_only=True)
    
    class Meta:
        model = ModerationAction
        fields = [
            'id',
            'moderator',
            'moderator_username',
            'action_type',
            'target_user',
            'target_user_username',
            'content_type',
            'object_id',
            'content_object',
            'description',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'moderator_username',
            'target_user_username',
            'created_at',
        ]


