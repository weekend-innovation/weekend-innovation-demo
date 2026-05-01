"""
選出機能のサービス層 — 公正なランダム選出

対象となる「提案者（投稿者以外・有効ユーザー）」の集合だけを決め、この集合から
標準ライブラリの random.sample で等確率・非復元抽出する。評価・地域・経験などで
ユーザーを事前に絞り込む機能は設けない。Selection.selection_criteria は常に {} を保存する。
匿名名が課題内で足りない場合は表示名 Anonymous を複数ユーザーに共通で割り当てる。
"""
from __future__ import annotations

import logging
import random
from typing import Any, Dict, List

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from challenges.models import Challenge
from proposals.models import AnonymousName

from .models import ChallengeUserAnonymousName, Selection, SelectionHistory
from .notifications import SelectionNotificationService

User = get_user_model()
logger = logging.getLogger(__name__)

# フォールバック匿名表示（複数ユーザーに同一 AnonymousName を指してよい）
FALLBACK_ANONYMOUS_DISPLAY = "Anonymous"


def _notify_selection_completed(selection_id: int) -> None:
    """選出のDBコミット後に通知メールを送る（同じトランザクション内で送らない）"""
    try:
        selection = Selection.objects.get(pk=selection_id)
    except Selection.DoesNotExist:
        logger.error("選出通知: Selection id=%s が存在しません", selection_id)
        return
    SelectionNotificationService.send_selection_notification(selection)


class SelectionService:
    """選出サービスクラス"""

    # -------------------------------------------------------------------------
    # 選出ユーザー集合（事前のスコア・属性によるフィルタは行わない）
    # -------------------------------------------------------------------------
    @staticmethod
    def get_eligible_users(challenge: Challenge) -> List[User]:
        """
        選出対象: アクティブな提案者のうち、当該課題の投稿者本人のみを除くユーザー。
        返却リストには属性による追加フィルタをかけない（偏り防止）。
        """
        try:
            qs = User.objects.filter(user_type="proposer", is_active=True).exclude(
                id=challenge.contributor_id
            )
            eligible_users = list(qs)
            logger.info(f"選出対象ユーザー数: {len(eligible_users)}")
            return eligible_users
        except Exception as e:
            logger.error(f"選出対象ユーザー取得エラー: {e}")
            return []

    # -------------------------------------------------------------------------
    # 選出本体: eligible から random.sample で等確率・non-replacement
    # -------------------------------------------------------------------------
    @staticmethod
    def create_selection(challenge: Challenge, required_count: int) -> Selection:
        """選出レコード作成（criteria は常に空 dict）"""
        try:
            with transaction.atomic():
                selection = Selection.objects.create(
                    challenge=challenge,
                    contributor=challenge.contributor,
                    required_count=required_count,
                    selection_criteria={},
                    status="pending",
                )
                logger.info(f"選出を作成しました: {selection.id}")
                return selection
        except Exception as e:
            logger.error(f"選出作成エラー: {e}")
            raise ValidationError(f"選出の作成に失敗しました: {str(e)}") from e

    @staticmethod
    def random_selection(challenge: Challenge, required_count: int) -> Selection:
        """
        eligible ユーザー集合から random.sample で required_count 人を等確率で選ぶ。
        """
        try:
            with transaction.atomic():
                eligible_users = SelectionService.get_eligible_users(challenge)

                if not eligible_users:
                    raise ValidationError("選出対象となるユーザーが存在しません")

                if len(eligible_users) < required_count:
                    logger.warning(
                        f"選出対象ユーザー数({len(eligible_users)})が要求人数({required_count})より少ない"
                    )
                    required_count = len(eligible_users)

                # --- コア: 均等ランダム（非復元抽出） ---
                selected_users = random.sample(eligible_users, required_count)

                selection = SelectionService.create_selection(
                    challenge=challenge,
                    required_count=required_count,
                )
                selection.selected_users.set(selected_users)
                selection.selected_count = len(selected_users)
                selection.status = "completed"
                selection.completed_at = timezone.now()
                selection.selection_method = "random"
                selection.save()

                SelectionService._assign_anonymous_names(challenge, selected_users)

                for user in selected_users:
                    SelectionHistory.objects.create(
                        selection=selection,
                        user=user,
                        action="selected",
                        reason="等確率ランダム選出（random.sample）",
                        metadata={
                            "selection_method": "random",
                            "challenge_id": challenge.id,
                        },
                    )

                logger.info(
                    f"ランダム選出完了: selection_id={selection.id}, "
                    f"選出人数={len(selected_users)}"
                )
                sid = selection.id
                transaction.on_commit(lambda sid=sid: _notify_selection_completed(sid))
                return selection
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"ランダム選出エラー: {e}")
            raise ValidationError(f"ランダム選出に失敗しました: {str(e)}") from e

    @staticmethod
    def _assign_anonymous_names(challenge: Challenge, users: List[User]) -> None:
        """課題に選出されたユーザーへ匿名名。プール枯渇時はすべて Anonymous にフォールバック。"""
        try:
            fallback, _ = AnonymousName.objects.get_or_create(
                name=FALLBACK_ANONYMOUS_DISPLAY,
                defaults={"category": "animal"},
            )

            pool_only = [
                n for n in AnonymousName.objects.exclude(pk=fallback.pk)
                if n.name != FALLBACK_ANONYMOUS_DISPLAY
            ]

            used_ids = set(
                ChallengeUserAnonymousName.objects.filter(challenge=challenge)
                .values_list("anonymous_name_id", flat=True)
            )
            available_pool = [n for n in pool_only if n.id not in used_ids]

            need = len(users)
            if len(available_pool) < need:
                logger.warning(
                    "匿名名プールがこの課題で必要人数に不足する可能性があります"
                    "（フォールバック Anonymous を割り当てます）:"
                    " 必要=%s 未使用プール=%s",
                    need,
                    len(available_pool),
                )

            random.shuffle(available_pool)
            assigned_reserved_ids = set(used_ids)

            for user in users:
                cands = [n for n in available_pool if n.id not in assigned_reserved_ids]
                if cands:
                    pick = cands[0]
                    anonymous_name = pick
                    assigned_reserved_ids.add(pick.id)
                else:
                    anonymous_name = fallback

                ChallengeUserAnonymousName.objects.update_or_create(
                    challenge=challenge,
                    user=user,
                    defaults={"anonymous_name": anonymous_name},
                )
                logger.info(
                    "匿名名割当: user=%s challenge=%s name=%s",
                    user.pk,
                    challenge.id,
                    anonymous_name.name,
                )
        except Exception as e:
            logger.error(f"匿名名割当エラー: {e}")

    # -------------------------------------------------------------------------

    @staticmethod
    def cancel_selection(selection: Selection, reason: str = "") -> bool:
        """選出をキャンセル"""
        try:
            with transaction.atomic():
                selection.status = "cancelled"
                selection.save()
                SelectionHistory.objects.create(
                    selection=selection,
                    user=selection.contributor,
                    action="removed",
                    reason=f"選出キャンセル: {reason}",
                    metadata={"cancelled_by": "contributor", "reason": reason},
                )
                logger.info(f"選出をキャンセルしました: {selection.id}")
                return True
        except Exception as e:
            logger.error(f"選出キャンセルエラー: {e}")
            return False

    @staticmethod
    def get_selection_statistics() -> Dict[str, Any]:
        """選出統計を取得"""
        try:
            total_selections = Selection.objects.count()
            completed_selections = Selection.objects.filter(status="completed").count()
            pending_selections = Selection.objects.filter(status="pending").count()
            cancelled_selections = Selection.objects.filter(status="cancelled").count()
            total_selected_users = (
                Selection.objects.aggregate(total=models.Sum("selected_count"))[
                    "total"
                ]
                or 0
            )
            avg_selection_size = (
                Selection.objects.filter(status="completed").aggregate(
                    avg=models.Avg("selected_count")
                )["avg"]
                or 0
            )
            return {
                "total_selections": total_selections,
                "completed_selections": completed_selections,
                "pending_selections": pending_selections,
                "cancelled_selections": cancelled_selections,
                "total_selected_users": total_selected_users,
                "average_selection_size": round(avg_selection_size, 2),
                "completion_rate": round(
                    (completed_selections / total_selections * 100)
                    if total_selections > 0
                    else 0,
                    2,
                ),
            }
        except Exception as e:
            logger.error(f"統計取得エラー: {e}")
            return {}
