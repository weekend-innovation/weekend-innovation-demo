"""
モデレーション管理のURL設定
"""
from django.urls import path
from . import views

app_name = 'moderation'

urlpatterns = [
    # 報告関連
    path('reports/', views.ReportListCreateView.as_view(), name='report-list-create'),
    path('reports/<int:pk>/', views.ReportDetailView.as_view(), name='report-detail'),
    path('reports/create/', views.create_report, name='create-report'),
    path('reports/check/', views.check_if_reported, name='check-if-reported'),
    path('content-types/', views.content_type_lookup, name='content-type-lookup'),
    
    # ユーザー利用停止関連
    path('suspensions/', views.UserSuspensionListCreateView.as_view(), name='suspension-list-create'),
    path('suspensions/<int:pk>/', views.UserSuspensionDetailView.as_view(), name='suspension-detail'),
    path('suspensions/status/', views.user_suspension_status, name='suspension-status'),
    
    # モデレーションアクション履歴
    path('actions/', views.ModerationActionListView.as_view(), name='action-list'),
    
    # 統計・管理機能
    path('stats/', views.report_stats, name='report-stats'),
    path('bulk-moderate/', views.bulk_moderate_reports, name='bulk-moderate'),
]


