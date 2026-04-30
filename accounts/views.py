"""
ユーザー認証・プロフィール管理のAPIビュー

Weekend Innovationプロジェクトの認証システム
"""

from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from django.contrib.auth import authenticate

from .models import User, ContributorProfile, ProposerProfile
from .serializers import (
    UserSerializer, 
    UserRegistrationSerializer, 
    UserLoginSerializer,
    UserDetailSerializer,
    ContributorProfileSerializer,
    ProposerProfileSerializer,
    ProfileUpdateSerializer,
    APP_USER_TYPES,
)


class RegisterView(generics.CreateAPIView):
    """
    ユーザー新規登録API
    投稿者・提案者の2つのユーザータイプに対応
    """
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer
    
    def create(self, request, *args, **kwargs):
        """
        ユーザーとプロフィールを作成
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # JWTトークン生成
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'ユーザー登録が完了しました',
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


class CheckRegistrationAvailabilityView(generics.GenericAPIView):
    """
    新規登録前の重複確認（基本情報用）
    メール・ユーザー名がアプリ登録用ユーザーで既に使われているかを返す
    """
    permission_classes = [AllowAny]

    def get(self, request):
        email = (request.query_params.get('email') or '').strip().lower()
        username = (request.query_params.get('username') or '').strip()

        result = {
            'email_available': True,
            'username_available': True,
        }
        if email and User.objects.filter(
            email__iexact=email,
            user_type__in=APP_USER_TYPES,
        ).exists():
            result['email_available'] = False
        if username and User.objects.filter(username=username).exists():
            result['username_available'] = False
        return Response(result)


class LoginView(generics.GenericAPIView):
    """
    ユーザーログインAPI
    ユーザー名とパスワードで認証
    """
    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer
    
    def post(self, request):
        """
        ログイン処理
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        
        # JWTトークン生成
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'ログインに成功しました',
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    ユーザープロフィール取得・更新API
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserDetailSerializer
    
    def get_object(self):
        """
        認証されたユーザーのプロフィールを取得
        """
        return self.request.user


class ContributorProfileView(generics.RetrieveUpdateAPIView):
    """
    投稿者プロフィール取得・更新API
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ContributorProfileSerializer
    
    def get_object(self):
        """
        認証されたユーザーの投稿者プロフィールを取得
        """
        if self.request.user.user_type != 'contributor':
            raise serializers.ValidationError("投稿者ユーザーではありません")
        
        try:
            return self.request.user.contributor_profile
        except ContributorProfile.DoesNotExist:
            raise serializers.ValidationError("プロフィールが見つかりません")


class ProposerProfileView(generics.RetrieveUpdateAPIView):
    """
    提案者プロフィール取得・更新API
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ProposerProfileSerializer
    
    def get_object(self):
        """
        認証されたユーザーの提案者プロフィールを取得
        """
        if self.request.user.user_type != 'proposer':
            raise serializers.ValidationError("提案者ユーザーではありません")
        
        try:
            return self.request.user.proposer_profile
        except ProposerProfile.DoesNotExist:
            raise serializers.ValidationError("プロフィールが見つかりません")


class LogoutView(generics.GenericAPIView):
    """
    ユーザーログアウトAPI
    """
    permission_classes = [AllowAny]  # ログアウトは認証不要に変更
    
    def post(self, request):
        """
        ログアウト処理（トークンをブラックリストに追加）
        """
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response({
                    'error': 'リフレッシュトークンが必要です'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # トークンの無効化はスキップ（フロントエンドでローカルログアウトを実行）
            # サーバー側でのトークン無効化は実装しない（フロントエンドでローカルログアウト）
            
            return Response({
                'message': 'ログアウトしました'
            }, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({
                'error': f'ログアウトに失敗しました: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


class RefreshTokenView(generics.GenericAPIView):
    """
    JWTリフレッシュトークン更新API
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        リフレッシュトークンでアクセストークンを更新
        """
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            
            return Response({
                'access': str(token.access_token),
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': 'トークンの更新に失敗しました'
            }, status=status.HTTP_400_BAD_REQUEST)