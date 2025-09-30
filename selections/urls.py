"""
選出機能のURL設定
"""
from django.urls import path
from . import views

urlpatterns = [
    # 選出の基本操作
    path('', views.SelectionListCreateView.as_view(), name='selection-list-create'),
    path('<int:pk>/', views.SelectionDetailView.as_view(), name='selection-detail'),
    
    # 選出実行
    path('execute/', views.SelectionExecuteView.as_view(), name='selection-execute'),
    
    # 選出履歴
    path('<int:selection_id>/history/', views.SelectionHistoryView.as_view(), name='selection-history'),
    
    # 選出統計
    path('statistics/', views.SelectionStatisticsView.as_view(), name='selection-statistics'),
    
    # 選出基準
    path('criteria/', views.SelectionCriteriaListView.as_view(), name='selection-criteria-list'),
    
    # その他の操作
    path('<int:selection_id>/cancel/', views.cancel_selection, name='selection-cancel'),
    path('challenges/<int:challenge_id>/eligible-users/', views.get_eligible_users, name='eligible-users'),
]

