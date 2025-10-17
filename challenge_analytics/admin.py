"""
課題分析・まとめ機能の管理画面
"""
from django.contrib import admin
from .models import ChallengeAnalysis, ProposalInsight


@admin.register(ChallengeAnalysis)
class ChallengeAnalysisAdmin(admin.ModelAdmin):
    """課題分析の管理画面"""
    
    list_display = [
        'challenge',
        'status',
        'total_proposals',
        'unique_proposers',
        'analyzed_at',
        'created_at'
    ]
    
    list_filter = [
        'status',
        'created_at',
        'analyzed_at'
    ]
    
    search_fields = [
        'challenge__title',
        'executive_summary'
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'analyzed_at'
    ]
    
    fieldsets = (
        ('基本情報', {
            'fields': ('challenge', 'status')
        }),
        ('統計情報', {
            'fields': ('total_proposals', 'unique_proposers')
        }),
        ('分析結果', {
            'fields': ('common_themes', 'innovative_solutions', 'feasibility_analysis')
        }),
        ('まとめ', {
            'fields': ('executive_summary', 'detailed_analysis', 'recommendations')
        }),
        ('メタデータ', {
            'fields': ('created_at', 'updated_at', 'analyzed_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ProposalInsight)
class ProposalInsightAdmin(admin.ModelAdmin):
    """提案洞察の管理画面"""
    
    list_display = [
        'analysis',
        'proposal_id',
        'innovation_score',
        'feasibility_score',
        'impact_score',
        'created_at'
    ]
    
    list_filter = [
        'analysis__challenge',
        'created_at'
    ]
    
    search_fields = [
        'analysis__challenge__title',
        'proposal_id'
    ]
    
    readonly_fields = [
        'created_at'
    ]
    
    fieldsets = (
        ('基本情報', {
            'fields': ('analysis', 'proposal_id')
        }),
        ('スコア', {
            'fields': ('innovation_score', 'feasibility_score', 'impact_score')
        }),
        ('分析内容', {
            'fields': ('key_themes', 'strengths', 'concerns')
        }),
        ('メタデータ', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )