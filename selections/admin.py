"""
選出機能の管理画面設定
"""
from django.contrib import admin
from .models import Selection, SelectionHistory, SelectionCriteria, ChallengeUserAnonymousName, UserEvaluationCompletion


@admin.register(Selection)
class SelectionAdmin(admin.ModelAdmin):
    """選出の管理画面設定"""
    list_display = ('id', 'challenge', 'contributor', 'required_count', 'selected_count', 'status', 'created_at')
    list_filter = ('status', 'selection_method', 'notification_sent', 'created_at', 'contributor__user_type')
    search_fields = ('challenge__title', 'contributor__username')
    raw_id_fields = ('challenge', 'contributor')
    filter_horizontal = ('selected_users',)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'completed_at')
    
    fieldsets = (
        (None, {
            'fields': ('challenge', 'contributor', 'required_count', 'selected_count')
        }),
        ('選出設定', {
            'fields': ('selection_method', 'selection_criteria')
        }),
        ('ステータス', {
            'fields': ('status', 'notification_sent')
        }),
        ('選出されたユーザー', {
            'fields': ('selected_users',),
            'classes': ('collapse',)
        }),
        ('タイムスタンプ', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('challenge', 'contributor')


@admin.register(SelectionHistory)
class SelectionHistoryAdmin(admin.ModelAdmin):
    """選出履歴の管理画面設定"""
    list_display = ('id', 'selection', 'user', 'action', 'created_at')
    list_filter = ('action', 'created_at', 'user__user_type')
    search_fields = ('selection__challenge__title', 'user__username')
    raw_id_fields = ('selection', 'user')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('selection', 'user', 'action', 'reason')
        }),
        ('メタデータ', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('タイムスタンプ', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(SelectionCriteria)
class SelectionCriteriaAdmin(admin.ModelAdmin):
    """選出基準の管理画面設定"""
    list_display = ('id', 'name', 'criteria_type', 'is_active', 'created_at')
    list_filter = ('criteria_type', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    date_hierarchy = 'created_at'
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'criteria_type')
        }),
        ('設定', {
            'fields': ('parameters', 'is_active')
        }),
        ('タイムスタンプ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ChallengeUserAnonymousName)
class ChallengeUserAnonymousNameAdmin(admin.ModelAdmin):
    """課題ユーザー匿名名の管理画面設定"""
    list_display = ('id', 'challenge', 'user', 'anonymous_name', 'created_at')
    list_filter = ('created_at', 'challenge')
    search_fields = ('challenge__title', 'user__username', 'anonymous_name__name')
    raw_id_fields = ('challenge', 'user', 'anonymous_name')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('challenge', 'user', 'anonymous_name')
        }),
        ('タイムスタンプ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('challenge', 'user', 'anonymous_name')


@admin.register(UserEvaluationCompletion)
class UserEvaluationCompletionAdmin(admin.ModelAdmin):
    """ユーザー評価完了状態の管理画面設定"""
    list_display = ('id', 'challenge', 'user', 'has_completed_all_evaluations', 'completed_at', 'created_at')
    list_filter = ('has_completed_all_evaluations', 'created_at', 'completed_at')
    search_fields = ('challenge__title', 'user__username')
    raw_id_fields = ('challenge', 'user')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('challenge', 'user')
        }),
        ('完了状態', {
            'fields': ('has_completed_all_evaluations', 'completed_at')
        }),
        ('タイムスタンプ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('challenge', 'user')