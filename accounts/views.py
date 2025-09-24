"""
ユーザー認証・プロフィール管理のAPIビュー

Weekend Innovationプロジェクトの認証システム
"""

from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

from .models import User, ContributorProfile, ProposerProfile
from .serializers import (
    UserSerializer, 
    UserRegistrationSerializer, 
    UserLoginSerializer,
    UserDetailSerializer,
    ContributorProfileSerializer,
    ProposerProfileSerializer,
    ProfileUpdateSerializer
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


class LoginView(generics.GenericAPIView):
    """
    ユーザーログインAPI
    メールアドレスとパスワードで認証
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
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        ログアウト処理（トークンをブラックリストに追加）
        """
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response({
                'message': 'ログアウトしました'
            }, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({
                'error': 'ログアウトに失敗しました'
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