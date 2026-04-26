"""
ユーザー認証・プロフィール管理のURL設定

Weekend Innovationプロジェクトの認証APIエンドポイント
"""

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # 認証関連
    path('check-registration/', views.CheckRegistrationAvailabilityView.as_view(), name='check-registration'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('refresh/', views.RefreshTokenView.as_view(), name='refresh'),
    
    # プロフィール関連
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('profile/contributor/', views.ContributorProfileView.as_view(), name='contributor-profile'),
    path('profile/proposer/', views.ProposerProfileView.as_view(), name='proposer-profile'),
]
