"""
ユーザー認証・プロフィール管理のシリアライザー

API通信でのデータシリアライゼーションを管理
"""

from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, ContributorProfile, ProposerProfile


class UserSerializer(serializers.ModelSerializer):
    """
    ユーザー基本情報のシリアライザー
    """
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'user_type', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ContributorProfileSerializer(serializers.ModelSerializer):
    """
    投稿者プロフィールのシリアライザー
    """
    class Meta:
        model = ContributorProfile
        fields = [
            'company_name', 'representative_name', 'address', 
            'phone_number', 'industry', 'employee_count', 
            'established_year', 'company_url', 'company_logo', 'location'
        ]


class ProposerProfileSerializer(serializers.ModelSerializer):
    """
    提案者プロフィールのシリアライザー
    """
    class Meta:
        model = ProposerProfile
        fields = [
            'full_name', 'gender', 'birth_date', 'address', 
            'phone_number', 'occupation', 'nationality', 
            'profile_image'
        ]


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    ユーザー新規登録用のシリアライザー
    """
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=True, allow_blank=False)
    profile = serializers.JSONField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm', 
            'user_type', 'profile'
        ]
    
    def validate(self, data):
        """
        パスワード確認とユーザータイプ別プロフィール検証
        """
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("パスワードが一致しません")
        if not data.get('email'):
            raise serializers.ValidationError("メールアドレスは必須です")
        data['email'] = data['email'].strip().lower()
        if User.objects.filter(email__iexact=data['email']).exists():
            raise serializers.ValidationError("このメールアドレスは既に使用されています")
        
        user_type = data.get('user_type')
        profile_data = data.get('profile', {})
        
        # ユーザータイプ別の必須フィールド検証
        if user_type == 'contributor':
            required_fields = ['company_name', 'representative_name', 'address', 'phone_number']
            for field in required_fields:
                if not profile_data.get(field):
                    raise serializers.ValidationError(f"投稿者プロフィールの{field}は必須です")
        
        return data
    
    def create(self, validated_data):
        """
        ユーザーとプロフィールを作成
        """
        profile_data = validated_data.pop('profile')
        validated_data.pop('password_confirm')
        
        # ユーザー作成
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            user_type=validated_data['user_type']
        )
        
        # プロフィール作成
        if user.user_type == 'contributor':
            ContributorProfile.objects.create(user=user, **profile_data)
        elif user.user_type == 'proposer':
            ProposerProfile.objects.create(user=user, **profile_data)
        
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    ユーザーログイン用のシリアライザー
    """
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, data):
        """
        認証情報の検証
        """
        email = data.get('email')
        password = data.get('password')
        
        if email and password:
            # メールアドレスで候補ユーザーを検索（重複メールにも対応）
            users = User.objects.filter(email=email)
            if not users.exists():
                raise serializers.ValidationError("ユーザーが存在しません")

            matched_users = []
            for candidate in users:
                authed_user = authenticate(
                    username=candidate.username,
                    password=password,
                )
                if authed_user:
                    matched_users.append(authed_user)

            if not matched_users:
                raise serializers.ValidationError("メールアドレスまたはパスワードが正しくありません")

            if len(matched_users) > 1:
                raise serializers.ValidationError(
                    "同じメールアドレス・同じパスワードのアカウントが複数あるためログインできません。"
                    "どちらかのパスワードまたはメールアドレスを変更してください。"
                )

            user = matched_users[0]
            if not user.is_active:
                raise serializers.ValidationError("アカウントが無効です")
            
            data['user'] = user
            return data
        else:
            raise serializers.ValidationError("メールアドレスとパスワードを入力してください")


class UserDetailSerializer(serializers.ModelSerializer):
    """
    ユーザー詳細情報のシリアライザー
    """
    contributor_profile = ContributorProfileSerializer(read_only=True)
    proposer_profile = ProposerProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'user_type', 
            'created_at', 'updated_at', 'contributor_profile', 'proposer_profile'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_email(self, value):
        normalized = value.strip().lower()
        qs = User.objects.filter(email__iexact=normalized)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("このメールアドレスは既に使用されています")
        return normalized


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """
    プロフィール更新用のシリアライザー
    """
    class Meta:
        model = None  # 動的に設定
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        profile_type = kwargs.pop('profile_type', None)
        super().__init__(*args, **kwargs)
        
        if profile_type == 'contributor':
            self.Meta.model = ContributorProfile
        elif profile_type == 'proposer':
            self.Meta.model = ProposerProfile
