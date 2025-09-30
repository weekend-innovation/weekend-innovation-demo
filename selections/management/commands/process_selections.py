"""
選出処理の管理コマンド
定期実行やバッチ処理用
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from selections.models import Selection
from selections.services import SelectionService
from selections.notifications import SelectionNotificationService


class Command(BaseCommand):
    help = '選出処理の管理コマンド'

    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            type=str,
            choices=['cleanup', 'reminders', 'statistics'],
            default='statistics',
            help='実行するアクション'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='処理対象の日数（デフォルト: 30日）'
        )

    def handle(self, *args, **options):
        action = options['action']
        days = options['days']

        if action == 'cleanup':
            self.cleanup_old_selections(days)
        elif action == 'reminders':
            self.send_reminders(days)
        elif action == 'statistics':
            self.show_statistics()

    def cleanup_old_selections(self, days):
        """古い選出データのクリーンアップ"""
        self.stdout.write(f'{days}日前の選出データをクリーンアップします...')
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # 完了済みの古い選出を取得
        old_selections = Selection.objects.filter(
            status='completed',
            completed_at__lt=cutoff_date
        )
        
        count = old_selections.count()
        if count > 0:
            old_selections.delete()
            self.stdout.write(
                self.style.SUCCESS(f'{count}件の古い選出データを削除しました')
            )
        else:
            self.stdout.write('削除対象のデータはありませんでした')

    def send_reminders(self, days):
        """選出リマインダーの送信"""
        self.stdout.write(f'{days}日以内の選出リマインダーを送信します...')
        
        # 期限が近い課題の選出を取得
        deadline_cutoff = timezone.now() + timedelta(days=days)
        
        active_selections = Selection.objects.filter(
            status='completed',
            challenge__deadline__lte=deadline_cutoff,
            challenge__deadline__gt=timezone.now(),
            notification_sent=True
        )
        
        sent_count = 0
        for selection in active_selections:
            if SelectionNotificationService.send_selection_reminder(selection):
                sent_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'{sent_count}件のリマインダーを送信しました')
        )

    def show_statistics(self):
        """選出統計の表示"""
        self.stdout.write('選出統計情報:')
        
        stats = SelectionService.get_selection_statistics()
        
        self.stdout.write(f'総選出数: {stats.get("total_selections", 0)}')
        self.stdout.write(f'完了済み: {stats.get("completed_selections", 0)}')
        self.stdout.write(f'選出中: {stats.get("pending_selections", 0)}')
        self.stdout.write(f'キャンセル済み: {stats.get("cancelled_selections", 0)}')
        self.stdout.write(f'総選出ユーザー数: {stats.get("total_selected_users", 0)}')
        self.stdout.write(f'平均選出人数: {stats.get("average_selection_size", 0)}')
        self.stdout.write(f'完了率: {stats.get("completion_rate", 0)}%')

