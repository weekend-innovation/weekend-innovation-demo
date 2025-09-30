from django.contrib import admin
from .models import Proposal, AnonymousName

# Register your models here.

@admin.register(AnonymousName)
class AnonymousNameAdmin(admin.ModelAdmin):
    """匿名名の管理画面設定"""
    list_display = ('name', 'category', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('name',)
    ordering = ('name',)

@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    """提案の管理画面設定"""
    list_display = ('id', 'conclusion', 'challenge', 'display_name', 'status', 'is_adopted', 'created_at')
    list_filter = ('status', 'is_adopted', 'is_anonymous', 'created_at', 'challenge__status')
    search_fields = ('conclusion', 'challenge__title', 'proposer__username', 'anonymous_name__name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('基本情報', {
            'fields': ('conclusion', 'reasoning', 'challenge', 'proposer')
        }),
        ('匿名化', {
            'fields': ('is_anonymous', 'anonymous_name')
        }),
        ('ステータス', {
            'fields': ('status', 'is_adopted')
        }),
        ('評価', {
            'fields': ('rating', 'rating_count')
        }),
        ('システム情報', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """クエリセットの最適化"""
        return super().get_queryset(request).select_related('challenge', 'proposer', 'anonymous_name')
    
    def display_name(self, obj):
        """表示名の表示"""
        return obj.display_name
    display_name.short_description = '表示名'