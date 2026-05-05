from django.contrib import admin
from .models import Challenge

# Register your models here.

@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    """課題の管理画面設定"""
    list_display = ('title', 'contributor', 'is_contributor_anonymous', 'status', 'reward_amount', 'adoption_reward', 'deadline', 'created_at')
    list_filter = ('status', 'is_contributor_anonymous', 'created_at', 'deadline')
    search_fields = ('title', 'description', 'contributor__username')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('基本情報', {
            'fields': ('title', 'description', 'contributor', 'is_contributor_anonymous')
        }),
        ('報酬・選出情報', {
            'fields': ('reward_amount', 'adoption_reward', 'required_participants')
        }),
        ('期限・ステータス', {
            'fields': ('deadline', 'status')
        }),
        ('システム情報', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """クエリセットの最適化"""
        return super().get_queryset(request).select_related('contributor')