"""
seed_adoption_verification_demo で作成したデモ課題のみを削除する。

タイトルが DEMO_TITLE_PREFIX で始まり、かつ指定投稿者が所有する Challenge を対象（CASCADE で選出・提案等も消える）。

--if-after-deadline: 2026-05-03 23:59:59 Asia/Tokyo より前なら何もしない（cron で毎日叩く想定）。
"""

from __future__ import annotations

from datetime import datetime

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from challenges.models import Challenge

from zoneinfo import ZoneInfo

User = get_user_model()

# seed_adoption_verification_demo.py と同じ値に保つこと
DEMO_TITLE_PREFIX = "【デモ採用確認・5/3削除予定】"


class Command(BaseCommand):
    help = "採用確認デモ課題（接頭辞付き）を投稿者単位で削除する"

    def add_arguments(self, parser):
        parser.add_argument(
            "--contributor-username",
            default="weekend-innovation-3",
            help="課題を所有する投稿者のユーザー名",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="削除対象の件数だけ表示し削除しない",
        )
        parser.add_argument(
            "--if-after-deadline",
            action="store_true",
            help=(
                "現在時刻が 2026-05-03 23:59:59 (Asia/Tokyo) より前なら終了。"
                "期限後のみ削除したいときに利用。"
            ),
        )

    def handle(self, *args, **options):
        if options["if_after_deadline"]:
            deadline = datetime(2026, 5, 3, 23, 59, 59, tzinfo=ZoneInfo("Asia/Tokyo"))
            if timezone.now() < deadline:
                self.stdout.write(
                    self.style.WARNING(
                        f"削除期限前のためスキップしました（削除は {deadline.isoformat()} 以降）。"
                    )
                )
                return

        username = options["contributor_username"]
        try:
            contributor = User.objects.get(username=username, user_type="contributor")
        except User.DoesNotExist:
            self.stderr.write(
                self.style.ERROR(f"投稿者ユーザー「{username}」が見つかりません。")
            )
            return

        qs = Challenge.objects.filter(
            contributor=contributor,
            title__startswith=DEMO_TITLE_PREFIX,
        )
        n = qs.count()
        if n == 0:
            self.stdout.write("削除対象の課題はありません。")
            return

        ids = list(qs.values_list("id", flat=True))
        if options["dry_run"]:
            self.stdout.write(
                self.style.WARNING(f"[dry-run] 削除予定 {n} 件: challenge_ids={ids}")
            )
            return

        deleted, details = qs.delete()
        self.stdout.write(
            self.style.SUCCESS(f"削除しました: {n} 課題（関連オブジェクト含む削除件数 {deleted}） ids={ids} / {details}")
        )
