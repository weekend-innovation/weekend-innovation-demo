from django.urls import path
from . import views

app_name = 'proposals'

urlpatterns = [
    # 提案一覧・作成
    path('', views.ProposalListCreateView.as_view(), name='proposal-list-create'),
    
    # 提案詳細・更新・削除
    path('<int:pk>/', views.ProposalDetailView.as_view(), name='proposal-detail'),
    
    # 提案詳細（コメント・評価情報を含む）
    path('<int:pk>/with-comments/', views.ProposalDetailWithCommentsView.as_view(), name='proposal-detail-with-comments'),
    
    # 特定課題の提案一覧
    path('challenge/<int:challenge_id>/', views.ProposalByChallengeView.as_view(), name='proposal-by-challenge'),
    
    # ユーザーの特定課題への提案状況確認
    path('user-challenge/<int:challenge_id>/', views.UserProposalForChallengeView.as_view(), name='user-proposal-for-challenge'),
    
    # 提案コメント関連
    path('<int:proposal_id>/comments/', views.ProposalCommentListCreateView.as_view(), name='proposal-comment-list-create'),
    
    # 提案評価
    path('<int:proposal_id>/evaluate/', views.ProposalEvaluationCreateView.as_view(), name='proposal-evaluation-create'),
    path('<int:proposal_id>/evaluation/', views.ProposalEvaluationRetrieveView.as_view(), name='proposal-evaluation-retrieve'),
    
    # コメント返信
    path('comments/<int:comment_id>/reply/', views.ProposalCommentReplyCreateView.as_view(), name='proposal-comment-reply-create'),
    
    # 提案参考
    path('<int:proposal_id>/reference/', views.ProposalReferenceCreateView.as_view(), name='proposal-reference-create'),
    
    # 解決案採用（投稿者のみ、期限切れ課題）
    path('<int:pk>/adopt/', views.ProposalAdoptView.as_view(), name='proposal-adopt'),
]
