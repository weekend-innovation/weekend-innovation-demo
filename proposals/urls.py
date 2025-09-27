from django.urls import path
from . import views

app_name = 'proposals'

urlpatterns = [
    # 提案一覧・作成
    path('', views.ProposalListCreateView.as_view(), name='proposal-list-create'),
    
    # 提案詳細・更新・削除
    path('<int:pk>/', views.ProposalDetailView.as_view(), name='proposal-detail'),
    
    # 提案採用
    path('<int:pk>/adopt/', views.ProposalAdoptionView.as_view(), name='proposal-adopt'),
    
    # 特定課題の提案一覧
    path('challenge/<int:challenge_id>/', views.ProposalByChallengeListView.as_view(), name='proposal-by-challenge'),
    
    # 提案コメント
    path('<int:proposal_id>/comments/', views.ProposalCommentListCreateView.as_view(), name='proposal-comment-list-create'),
    
    # 提案評価
    path('<int:proposal_id>/evaluations/', views.ProposalEvaluationListCreateView.as_view(), name='proposal-evaluation-list-create'),
    path('<int:proposal_id>/evaluations/<int:pk>/', views.ProposalEvaluationDetailView.as_view(), name='proposal-evaluation-detail'),
]
