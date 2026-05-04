"""
モデレーション管理の管理画面設定
"""
from datetime import timedelta

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import ModerationAction, Report, UserSuspension
from . import services


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """報告管理画面"""

    list_display = [
        "id",
        "reporter",
        "content_type_name",
        "object_id",
        "reported_user_display",
        "context_admin_links_short",
        "reason",
        "status",
        "created_at",
        "moderator",
    ]
    list_filter = ["status", "reason", "content_type", "created_at"]
    search_fields = ["reporter__username", "reporter__email", "description", "moderator_notes"]
    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "resolved_at",
        "reported_user_display",
        "context_admin_links",
        "reported_content_preview",
    ]
    raw_id_fields = ["reporter", "moderator"]

    fieldsets = (
        (
            "基本情報",
            {
                "fields": (
                    "id",
                    "reporter",
                    "content_type",
                    "object_id",
                    "reported_user_display",
                    "context_admin_links",
                )
            },
        ),
        ("報告対象の内容", {"fields": ("reported_content_preview",)}),
        ("報告内容", {"fields": ("reason", "description")}),
        ("審査情報", {"fields": ("status", "moderator", "moderator_notes")}),
        ("タイムスタンプ", {"fields": ("created_at", "updated_at", "resolved_at"), "classes": ("collapse",)}),
    )

    def content_type_name(self, obj):
        """コンテンツタイプ名を表示"""
        return obj.get_content_type_name()

    content_type_name.short_description = "コンテンツタイプ"

    def _get_related_proposal(self, obj):
        """通報オブジェクトから親 Proposal を解決（解決案・コメント・返信のいずれでも）"""
        model = obj.content_type.model
        oid = obj.object_id
        try:
            from proposals.models import Proposal, ProposalComment, ProposalCommentReply

            if model == "proposal":
                return Proposal.objects.filter(pk=oid).first()
            if model == "proposalcomment":
                comment = ProposalComment.objects.select_related("proposal").filter(pk=oid).first()
                return comment.proposal if comment else None
            if model == "proposalcommentreply":
                reply = (
                    ProposalCommentReply.objects.select_related("comment__proposal").filter(pk=oid).first()
                )
                return reply.comment.proposal if reply else None
        except Exception:
            return None
        return None

    def context_admin_links(self, obj):
        """モデレーション用: 親解決案および通報直対象オブジェクトへの管理画面リンク"""
        proposal = self._get_related_proposal(obj)
        model = obj.content_type.model
        oid = obj.object_id
        chunks = []
        if proposal:
            url = reverse("admin:proposals_proposal_change", args=[proposal.pk])
            chunks.append(
                format_html(
                    '<a href="{}">解決案 #{}（一覧・インラインでコメント/返信）</a>', url, proposal.pk
                )
            )
        elif model != "proposal":
            chunks.append("親解決案を解決できませんでした")

        try:
            if model == "proposalcomment":
                url = reverse("admin:proposals_proposalcomment_change", args=[oid])
                chunks.append(format_html(' / <a href="{}">通報対象コメント #{}</a>', url, oid))
            elif model == "proposalcommentreply":
                url = reverse("admin:proposals_proposalcommentreply_change", args=[oid])
                chunks.append(format_html(' / <a href="{}">通報対象返信 #{}</a>', url, oid))
        except Exception:
            pass

        if not chunks:
            return "-"

        merged = chunks[0]
        for piece in chunks[1:]:
            merged = format_html("{}{}", merged, piece)
        return merged

    context_admin_links.short_description = "関連解決案・通報オブジェクトへのリンク"

    def context_admin_links_short(self, obj):
        proposal = self._get_related_proposal(obj)
        if not proposal:
            return "-"
        url = reverse("admin:proposals_proposal_change", args=[proposal.pk])
        return format_html('<a href="{}">#{}</a>', url, proposal.pk)

    context_admin_links_short.short_description = "解決案"

    def _resolve_target(self, obj):
        model = obj.content_type.model
        oid = obj.object_id
        try:
            if model == "proposal":
                from proposals.models import Proposal

                p = Proposal.objects.select_related("proposer").get(id=oid)
                preview = (p.conclusion or "")[:120]
                return p.proposer, f"解決案: {preview}"
            if model == "proposalcomment":
                from proposals.models import ProposalComment

                c = ProposalComment.objects.select_related("commenter").get(id=oid)
                snippet = (
                    ((c.conclusion or "")[:60] + " / " + (c.reasoning or "")[:60]).strip()
                )[:120]
                return c.commenter, f"コメント: {snippet}"
            if model == "proposalcommentreply":
                from proposals.models import ProposalCommentReply

                r = ProposalCommentReply.objects.select_related("replier").get(id=oid)
                preview = (r.content or "")[:120]
                return r.replier, f"返信: {preview}"
        except Exception:
            return None, "対象コンテンツを取得できませんでした。"
        return None, f"対象モデル: {model} / object_id={oid}"

    def reported_user_display(self, obj):
        user, _ = self._resolve_target(obj)
        if user:
            return f"{user.username} (id={user.id})"
        return "不明"

    reported_user_display.short_description = "通報対象ユーザー"

    def reported_content_preview(self, obj):
        _, preview = self._resolve_target(obj)
        return preview

    reported_content_preview.short_description = "通報対象の内容"

    def get_queryset(self, request):
        """クエリセットの最適化"""
        return super().get_queryset(request).select_related("reporter", "moderator", "content_type")

    # @admin.action だけでは一覧に出ない環境があるため明示列挙（通報レコード削除は delete_selected を維持）
    actions = [
        "suspend_target_users_30_days",
        "suspend_target_users_90_days",
        "suspend_target_users_180_days",
        "suspend_target_users_365_days",
        "delete_target_users_from_reports",
        "delete_selected",
    ]

    @admin.action(description="通報対象ユーザーを約1か月（30日間）利用停止する")
    def suspend_target_users_30_days(self, request, queryset):
        services.apply_suspension_from_reports(
            queryset, request.user, timedelta(days=30), request, "約1か月（30日）"
        )

    @admin.action(description="通報対象ユーザーを約3か月（90日間）利用停止する")
    def suspend_target_users_90_days(self, request, queryset):
        services.apply_suspension_from_reports(
            queryset, request.user, timedelta(days=90), request, "約3か月（90日）"
        )

    @admin.action(description="通報対象ユーザーを約6か月（180日間）利用停止する")
    def suspend_target_users_180_days(self, request, queryset):
        services.apply_suspension_from_reports(
            queryset, request.user, timedelta(days=180), request, "約6か月（180日）"
        )

    @admin.action(description="通報対象ユーザーを約1年（365日間）利用停止する")
    def suspend_target_users_365_days(self, request, queryset):
        services.apply_suspension_from_reports(
            queryset, request.user, timedelta(days=365), request, "約1年（365日）"
        )

    @admin.action(
        description="⚠ 通報対象ユーザーを削除（スタッフ・本人は除外／取り返し不可）"
    )
    def delete_target_users_from_reports(self, request, queryset):
        services.delete_target_users_from_reports(queryset, request.user, request)


@admin.register(UserSuspension)
class UserSuspensionAdmin(admin.ModelAdmin):
    """ユーザー利用停止管理画面"""

    list_display = [
        "id",
        "user",
        "reason",
        "status",
        "suspended_from",
        "suspended_until",
        "is_active_display",
        "moderator",
    ]
    list_filter = ["status", "reason", "suspended_from", "suspended_until"]
    search_fields = ["user__username", "user__email", "description"]
    readonly_fields = ["id", "created_at", "updated_at", "lifted_at", "is_active_display", "days_remaining_display"]
    raw_id_fields = ["user", "moderator"]
    filter_horizontal = ["related_reports"]

    fieldsets = (
        ("基本情報", {"fields": ("id", "user", "reason", "description")}),
        ("停止期間", {"fields": ("suspended_from", "suspended_until", "status")}),
        ("管理情報", {"fields": ("moderator", "related_reports")}),
        ("状態情報", {"fields": ("is_active_display", "days_remaining_display"), "classes": ("collapse",)}),
        ("タイムスタンプ", {"fields": ("created_at", "updated_at", "lifted_at"), "classes": ("collapse",)}),
    )

    def is_active_display(self, obj):
        """停止状態を色付きで表示"""
        if obj.is_active:
            return format_html('<span style="color: red; font-weight: bold;">停止中</span>')
        return format_html('<span style="color: green;">停止解除</span>')

    is_active_display.short_description = "停止状態"

    def days_remaining_display(self, obj):
        """残り日数を表示"""
        if obj.is_active:
            return f"{obj.days_remaining}日"
        return "-"

    days_remaining_display.short_description = "残り日数"

    def get_queryset(self, request):
        """クエリセットの最適化"""
        return super().get_queryset(request).select_related("user", "moderator").prefetch_related("related_reports")


@admin.register(ModerationAction)
class ModerationActionAdmin(admin.ModelAdmin):
    """モデレーションアクション履歴管理画面"""

    list_display = ["id", "action_type", "moderator", "target_user", "created_at", "description_short"]
    list_filter = ["action_type", "created_at"]
    search_fields = ["moderator__username", "target_user__username", "description"]
    readonly_fields = ["id", "created_at"]
    raw_id_fields = ["moderator", "target_user"]

    fieldsets = (
        ("基本情報", {"fields": ("id", "action_type", "moderator", "target_user")}),
        ("対象コンテンツ", {"fields": ("content_type", "object_id"), "classes": ("collapse",)}),
        ("詳細", {"fields": ("description",)}),
        ("タイムスタンプ", {"fields": ("created_at",)}),
    )

    def description_short(self, obj):
        """説明文を短縮表示"""
        if len(obj.description) > 50:
            return obj.description[:50] + "..."
        return obj.description

    description_short.short_description = "説明"

    def get_queryset(self, request):
        """クエリセットの最適化"""
        return super().get_queryset(request).select_related("moderator", "target_user", "content_type")

    def has_add_permission(self, request):
        """追加権限を無効化（API経由でのみ作成）"""
        return False
