"""
モデレーション管理の管理画面設定
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import Report, UserSuspension, ModerationAction


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """報告管理画面"""
    
    list_display = [
        'id', 'reporter', 'content_type_name', 'object_id', 
        'reason', 'status', 'created_at', 'moderator'
    ]
    list_filter = [
        'status', 'reason', 'content_type', 'created_at'
    ]
    search_fields = [
        'reporter__username', 'reporter__email', 
        'description', 'moderator_notes'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'resolved_at'
    ]
    raw_id_fields = ['reporter', 'moderator']
    
    fieldsets = (
        ('基本情報', {
            'fields': ('id', 'reporter', 'content_type', 'object_id')
        }),
        ('報告内容', {
            'fields': ('reason', 'description')
        }),
        ('審査情報', {
            'fields': ('status', 'moderator', 'moderator_notes')
        }),
        ('タイムスタンプ', {
            'fields': ('created_at', 'updated_at', 'resolved_at'),
            'classes': ('collapse',)
        }),
    )
    
    def content_type_name(self, obj):
        """コンテンツタイプ名を表示"""
        return obj.get_content_type_name()
    content_type_name.short_description = 'コンテンツタイプ'
    
    def get_queryset(self, request):
        """クエリセットの最適化"""
        return super().get_queryset(request).select_related(
            'reporter', 'moderator', 'content_type'
        )


@admin.register(UserSuspension)
class UserSuspensionAdmin(admin.ModelAdmin):
    """ユーザー利用停止管理画面"""
    
    list_display = [
        'id', 'user', 'reason', 'status', 
        'suspended_from', 'suspended_until', 
        'is_active_display', 'moderator'
    ]
    list_filter = [
        'status', 'reason', 'suspended_from', 'suspended_until'
    ]
    search_fields = [
        'user__username', 'user__email', 
        'description'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'lifted_at', 
        'is_active_display', 'days_remaining_display'
    ]
    raw_id_fields = ['user', 'moderator']
    filter_horizontal = ['related_reports']
    
    fieldsets = (
        ('基本情報', {
            'fields': ('id', 'user', 'reason', 'description')
        }),
        ('停止期間', {
            'fields': ('suspended_from', 'suspended_until', 'status')
        }),
        ('管理情報', {
            'fields': ('moderator', 'related_reports')
        }),
        ('状態情報', {
            'fields': ('is_active_display', 'days_remaining_display'),
            'classes': ('collapse',)
        }),
        ('タイムスタンプ', {
            'fields': ('created_at', 'updated_at', 'lifted_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_active_display(self, obj):
        """停止状態を色付きで表示"""
        if obj.is_active:
            return format_html(
                '<span style="color: red; font-weight: bold;">停止中</span>'
            )
        else:
            return format_html(
                '<span style="color: green;">停止解除</span>'
            )
    is_active_display.short_description = '停止状態'
    
    def days_remaining_display(self, obj):
        """残り日数を表示"""
        if obj.is_active:
            return f"{obj.days_remaining}日"
        else:
            return "-"
    days_remaining_display.short_description = '残り日数'
    
    def get_queryset(self, request):
        """クエリセットの最適化"""
        return super().get_queryset(request).select_related(
            'user', 'moderator'
        ).prefetch_related('related_reports')


@admin.register(ModerationAction)
class ModerationActionAdmin(admin.ModelAdmin):
    """モデレーションアクション履歴管理画面"""
    
    list_display = [
        'id', 'action_type', 'moderator', 'target_user', 
        'created_at', 'description_short'
    ]
    list_filter = [
        'action_type', 'created_at'
    ]
    search_fields = [
        'moderator__username', 'target_user__username', 
        'description'
    ]
    readonly_fields = [
        'id', 'created_at'
    ]
    raw_id_fields = ['moderator', 'target_user']
    
    fieldsets = (
        ('基本情報', {
            'fields': ('id', 'action_type', 'moderator', 'target_user')
        }),
        ('対象コンテンツ', {
            'fields': ('content_type', 'object_id'),
            'classes': ('collapse',)
        }),
        ('詳細', {
            'fields': ('description',)
        }),
        ('タイムスタンプ', {
            'fields': ('created_at',)
        }),
    )
    
    def description_short(self, obj):
        """説明文を短縮表示"""
        if len(obj.description) > 50:
            return obj.description[:50] + "..."
        return obj.description
    description_short.short_description = '説明'
    
    def get_queryset(self, request):
        """クエリセットの最適化"""
        return super().get_queryset(request).select_related(
            'moderator', 'target_user', 'content_type'
        )
    
    def has_add_permission(self, request):
        """追加権限を無効化（API経由でのみ作成）"""
        return False