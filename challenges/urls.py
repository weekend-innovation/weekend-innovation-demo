from django.urls import path
from . import views

app_name = 'challenges'

urlpatterns = [
    # 課題一覧・作成
    path('', views.ChallengeListCreateView.as_view(), name='challenge-list-create'),
    
    # 課題詳細・更新・削除
    path('<int:pk>/', views.ChallengeDetailView.as_view(), name='challenge-detail'),
    
    # 課題ステータス更新
    path('<int:pk>/status/', views.ChallengeStatusUpdateView.as_view(), name='challenge-status-update'),
    
    # 公開課題一覧（認証不要）
    path('public/', views.PublicChallengeListView.as_view(), name='public-challenge-list'),
    
    # 提案報酬計算
    path('calculate-reward/', views.calculate_proposal_reward, name='calculate-proposal-reward'),
]
