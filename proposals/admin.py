from django.contrib import admin
from .models import Proposal, ProposalComment, ProposalEvaluation

# Register your models here.

@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    """提案の管理画面設定"""
    list_display = ('id', 'challenge', 'proposer', 'is_adopted', 'evaluation_count', 'created_at')
    list_filter = ('is_adopted', 'is_deleted', 'created_at', 'challenge__status')
    search_fields = ('challenge__title', 'proposer__username', 'conclusion')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('基本情報', {
            'fields': ('challenge', 'proposer', 'conclusion', 'reasoning')
        }),
        ('ステータス', {
            'fields': ('is_adopted', 'is_deleted')
        }),
        ('システム情報', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """クエリセットの最適化"""
        return super().get_queryset(request).select_related('challenge', 'proposer')
    
    def evaluation_count(self, obj):
        """評価数の表示"""
        return obj.evaluations.count()
    evaluation_count.short_description = '評価数'

@admin.register(ProposalComment)
class ProposalCommentAdmin(admin.ModelAdmin):
    """提案コメントの管理画面設定"""
    list_display = ('id', 'proposal', 'commenter', 'target_section', 'is_deleted', 'created_at')
    list_filter = ('target_section', 'is_deleted', 'created_at')
    search_fields = ('proposal__challenge__title', 'commenter__username', 'conclusion')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    fieldsets = (
        ('基本情報', {
            'fields': ('proposal', 'commenter', 'target_section')
        }),
        ('コメント内容', {
            'fields': ('conclusion', 'reasoning')
        }),
        ('ステータス', {
            'fields': ('is_deleted',)
        }),
        ('システム情報', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """クエリセットの最適化"""
        return super().get_queryset(request).select_related('proposal__challenge', 'commenter')

@admin.register(ProposalEvaluation)
class ProposalEvaluationAdmin(admin.ModelAdmin):
    """提案評価の管理画面設定"""
    list_display = ('id', 'proposal', 'evaluator', 'evaluation', 'created_at')
    list_filter = ('evaluation', 'created_at')
    search_fields = ('proposal__challenge__title', 'evaluator__username')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    fieldsets = (
        ('基本情報', {
            'fields': ('proposal', 'evaluator', 'evaluation')
        }),
        ('システム情報', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """クエリセットの最適化"""
        return super().get_queryset(request).select_related('proposal__challenge', 'evaluator')