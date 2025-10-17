"""
課題分析・まとめ機能のURL設定
"""
from django.urls import path
from . import views

app_name = 'challenge_analytics'

urlpatterns = [
    # 分析結果の詳細取得
    path('challenges/<int:challenge_id>/analysis/', 
         views.ChallengeAnalysisDetailView.as_view(), 
         name='analysis-detail'),
    
    # 提案洞察の一覧取得
    path('challenges/<int:challenge_id>/insights/', 
         views.ProposalInsightListView.as_view(), 
         name='proposal-insights'),
    
    # 分析の手動実行
    path('challenges/<int:challenge_id>/analyze/', 
         views.trigger_analysis, 
         name='trigger-analysis'),
    
    # 分析ステータスの確認
    path('challenges/<int:challenge_id>/analysis/status/', 
         views.analysis_status, 
         name='analysis-status'),
    
    # 分析のリセット（開発用）
    path('challenges/<int:challenge_id>/analysis/reset/', 
         views.reset_analysis, 
         name='reset-analysis'),
    
    # クラスタリング結果の取得
    path('challenges/<int:challenge_id>/clustering/', 
         views.get_proposal_clustering, 
         name='proposal-clustering'),
]
