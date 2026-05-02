from django.contrib import admin
from django.utils.html import format_html

from .models import (
    AnonymousName,
    Proposal,
    ProposalComment,
    ProposalCommentReply,
    ProposalEditReference,
)


class ProposalCommentReplyInline(admin.TabularInline):
    """コメント詳細での返信スレッド（モデレーション用）"""

    model = ProposalCommentReply
    extra = 0
    fk_name = "comment"
    ordering = ("created_at",)
    verbose_name_plural = "返信"


class ProposalCommentInline(admin.TabularInline):
    """解決案詳細でのコメント＋返信の要約（流れ確認用）"""

    model = ProposalComment
    extra = 0
    fk_name = "proposal"
    can_delete = False
    ordering = ("created_at",)
    show_change_link = True
    verbose_name_plural = "コメント（結論・返信の一覧）"

    readonly_fields = (
        "target_section",
        "conclusion_excerpt",
        "replies_excerpt",
        "commenter",
        "created_at",
    )

    fields = readonly_fields + ("is_deleted",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("commenter").prefetch_related("replies")

    @admin.display(description="結論（抜粋）")
    def conclusion_excerpt(self, obj):
        text = obj.conclusion or ""
        ell = "…" if len(text) > 120 else ""
        return text[:120] + ell

    @admin.display(description="返信（一覧）")
    def replies_excerpt(self, obj):
        if not obj.pk:
            return "-"
        parts = []
        for r in obj.replies.all():
            body = r.content or ""
            tail = "…" if len(body) > 80 else ""
            parts.append(format_html("#{id}&nbsp;: {snippet}{tail}", id=r.pk, snippet=body[:80], tail=tail))
        if not parts:
            return "（返信なし）"
        merged = parts[0]
        for piece in parts[1:]:
            merged = format_html("{}<br>{}", merged, piece)
        return merged


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

    inlines = (ProposalCommentInline,)

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


@admin.register(ProposalComment)
class ProposalCommentAdmin(admin.ModelAdmin):
    list_display = ("id", "proposal", "commenter", "target_section", "created_at", "is_deleted")
    list_filter = ("target_section", "is_deleted", "created_at")
    search_fields = ("conclusion", "reasoning")
    ordering = ("-created_at",)
    raw_id_fields = ("proposal", "commenter")
    readonly_fields = ("created_at",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "proposal",
                    "commenter",
                    "target_section",
                    "conclusion",
                    "reasoning",
                    "is_deleted",
                    "is_read",
                    "created_at",
                )
            },
        ),
    )
    inlines = (ProposalCommentReplyInline,)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("proposal", "commenter")


@admin.register(ProposalCommentReply)
class ProposalCommentReplyAdmin(admin.ModelAdmin):
    list_display = ("id", "comment", "replier", "created_at", "is_deleted")
    list_filter = ("is_deleted", "created_at")
    search_fields = ("content",)
    ordering = ("-created_at",)
    raw_id_fields = ("comment", "replier")


@admin.register(ProposalEditReference)
class ProposalEditReferenceAdmin(admin.ModelAdmin):
    """解決案編集参考の管理"""
    list_display = ('id', 'proposal', 'comment', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('proposal__id', 'comment__id')
    ordering = ('-created_at',)