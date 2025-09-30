from django.urls import path
from . import views

app_name = 'proposals'

urlpatterns = [
    # 提案一覧・作成
    path('', views.ProposalListCreateView.as_view(), name='proposal-list-create'),
    
    # 提案詳細・更新・削除
    path('<int:pk>/', views.ProposalDetailView.as_view(), name='proposal-detail'),
    
    # 特定課題の提案一覧
    path('challenge/<int:challenge_id>/', views.ProposalByChallengeView.as_view(), name='proposal-by-challenge'),
    
    # ユーザーの特定課題への提案状況確認
    path('user-challenge/<int:challenge_id>/', views.UserProposalForChallengeView.as_view(), name='user-proposal-for-challenge'),
]
