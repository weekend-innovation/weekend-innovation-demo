"""
通報（Report）処理用のモデレーションヘルパ。
管理画面アクションおよびAPIから再利用可能な最小限の共通処理のみ。
"""

from __future__ import annotations

from collections import defaultdict
from typing import Optional
from datetime import timedelta

from django.contrib import messages as django_messages
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from proposals.models import Proposal, ProposalComment, ProposalCommentReply

from .models import ModerationAction, Report, UserSuspension

User = get_user_model()

# Report.reason → UserSuspension.reason（共通キーをそのまま使う／無ければ multiple_violations）
REPORT_REASON_TO_SUSPENSION_REASON = {
    "spam": "spam",
    "harassment": "harassment",
    "inappropriate_content": "inappropriate_content",
    "violence": "violence",
    "hate_speech": "hate_speech",
    "copyright": "copyright",
    "fake_news": "fake_news",
    "other": "other",
}


def resolve_report_target_user(report: Report) -> tuple[Optional[User], str]:
    """
    通報の content_type / object_id から「秩序を乱したと判断する」対象ユーザーを解決する。
    proposal → proposer, proposalcomment → commenter, proposalcommentreply → replier
    """
    model = report.content_type.model
    oid = report.object_id
    try:
        if model == "proposal":
            p = Proposal.objects.select_related("proposer").get(pk=oid)
            preview = (p.conclusion or "")[:120]
            return p.proposer, f"解決案: {preview}"
        if model == "proposalcomment":
            c = ProposalComment.objects.select_related("commenter").get(pk=oid)
            snippet = (
                ((c.conclusion or "")[:60] + " / " + (c.reasoning or "")[:60]).strip()
            )[:120]
            return c.commenter, f"コメント: {snippet}"
        if model == "proposalcommentreply":
            r = ProposalCommentReply.objects.select_related("replier").get(pk=oid)
            preview = (r.content or "")[:120]
            return r.replier, f"返信: {preview}"
        if model == "user":
            u = User.objects.get(pk=oid)
            return u, f"ユーザー: {u.username}"
    except Exception:
        return None, "対象コンテンツを取得できませんでした。"
    return None, f"未対応モデル: {model} (object_id={oid})"


def group_reports_by_target_user(
    queryset,
) -> tuple[dict[User, list[Report]], list[tuple[int, str]]]:
    """報告 QuerySet を対象ユーザーごとにまとめる。"""
    by_user: dict[User, list[Report]] = defaultdict(list)
    unresolvable: list[tuple[int, str]] = []
    for r in queryset.select_related("content_type", "reporter"):
        u, preview = resolve_report_target_user(r)
        if u is None:
            unresolvable.append((r.pk, preview))
        else:
            by_user[u].append(r)
    return by_user, unresolvable


@transaction.atomic
def apply_suspension_from_reports(
    queryset,
    moderator,
    duration: timedelta,
    request,
    label: str,
) -> int:
    """
    選択した報告ごとに対象ユーザーを利用停止する。
    既に有効な停止がある場合は suspended_until を長い方に延長する。
    対象報告は resolved にし、UserSuspension.related_reports に紐づける。
    戻り値: 停止を適用したユーザー数
    """
    by_user, bad = group_reports_by_target_user(queryset)
    for rid, msg in bad:
        django_messages.warning(request, f"報告 #{rid}: 対象ユーザーを解決できません ({msg})")

    now = timezone.now()
    applied = 0
    for user, reports in by_user.items():
        if user.is_superuser or user.is_staff:
            django_messages.warning(
                request,
                f'「{user.username}」はスタッフのため利用停止をスキップしました。',
            )
            continue

        r0 = reports[0]
        susp_reason = REPORT_REASON_TO_SUSPENSION_REASON.get(r0.reason, "multiple_violations")
        until = now + duration
        report_ids = ", ".join(str(x.pk) for x in reports)
        desc_add = (
            f"管理画面の通報一括処理（{label}）\n"
            f"報告ID: {report_ids}\n"
            f"停止終了予定: {until.isoformat()}"
        )

        active = (
            UserSuspension.objects.filter(user=user, status="active", suspended_until__gt=now)
            .order_by("-suspended_until")
            .first()
        )
        if active:
            if until > active.suspended_until:
                active.suspended_until = until
            active.description = f"{active.description}\n---\n{desc_add}".strip()
            active.moderator = moderator
            active.save()
            active.related_reports.add(*reports)
            sus = active
            final_until = active.suspended_until
        else:
            sus = UserSuspension.objects.create(
                user=user,
                reason=susp_reason,
                description=desc_add,
                suspended_from=now,
                suspended_until=until,
                status="active",
                moderator=moderator,
            )
            sus.related_reports.add(*reports)
            final_until = until

        note = f"[管理画面] 利用停止（{label}）〜 {final_until.isoformat()}"
        for rep in reports:
            rep.status = "resolved"
            rep.moderator = moderator
            rep.resolved_at = now
            rep.moderator_notes = (
                f"{rep.moderator_notes}\n{note}".strip() if rep.moderator_notes else note
            )
            rep.save()

        ModerationAction.objects.create(
            moderator=moderator,
            action_type="user_suspended",
            target_user=user,
            description=f"通報処理による利用停止（{label}）。終了予定 {final_until}。報告: {report_ids}",
        )
        applied += 1
        django_messages.success(
            request,
            f"「{user.username}」を {label} 利用停止しました（終了予定: {final_until.date()}）。",
        )
    return applied


@transaction.atomic
def delete_target_users_from_reports(queryset, moderator, request) -> int:
    """
    報告から解決した対象ユーザーを削除する（不可逆）。
    スタッフ・スーパーユーザー・操作者本人はスキップ。
    """
    by_user, bad = group_reports_by_target_user(queryset)
    for rid, msg in bad:
        django_messages.warning(request, f"報告 #{rid}: 対象ユーザーを解決できません ({msg})")

    deleted = 0
    for user, reports in by_user.items():
        if user.pk == moderator.pk:
            django_messages.error(request, "自分自身は削除できません。")
            continue
        if user.is_superuser or user.is_staff:
            django_messages.warning(
                request,
                f"「{user.username}」はスタッフのため削除をスキップしました。",
            )
            continue

        username = user.username
        uid = user.pk
        report_ids = ", ".join(str(x.pk) for x in reports)
        now = timezone.now()
        note = "[管理画面] 通報処理により対象ユーザーアカウントを削除"

        ModerationAction.objects.create(
            moderator=moderator,
            action_type="user_deleted",
            target_user=user,
            description=(
                f"通報処理によりユーザー削除。username={username}, id={uid}, 報告ID={report_ids}"
            ),
        )

        for rep in reports:
            rep.status = "resolved"
            rep.moderator = moderator
            rep.resolved_at = now
            rep.moderator_notes = (
                f"{rep.moderator_notes}\n{note}".strip() if rep.moderator_notes else note
            )
            rep.save()

        user.delete()
        deleted += 1
        django_messages.success(request, f"ユーザー「{username}」(id={uid}) を削除しました。")

    return deleted
