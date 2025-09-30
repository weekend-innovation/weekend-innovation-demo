"""
既存の課題の期限時間を23:59に更新する管理コマンド
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from challenges.models import Challenge
from datetime import datetime, time

class Command(BaseCommand):
    help = '既存の課題の期限時間を23:59に更新します'

    def handle(self, *args, **options):
        self.stdout.write('課題の期限時間を23:59に更新中...')
        
        updated_count = 0
        
        for challenge in Challenge.objects.all():
            # 現在の期限から日付部分のみを取得
            current_deadline = challenge.deadline
            date_part = current_deadline.date()
            
            # 時間を23:59に設定
            new_deadline = datetime.combine(date_part, time(23, 59))
            
            # タイムゾーンを考慮して更新
            if timezone.is_aware(current_deadline):
                new_deadline = timezone.make_aware(new_deadline)
            
            challenge.deadline = new_deadline
            challenge.save()
            
            updated_count += 1
            
            self.stdout.write(
                f'課題 "{challenge.title}" の期限を {new_deadline.strftime("%Y-%m-%d %H:%M")} に更新しました'
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'完了: {updated_count}件の課題の期限時間を23:59に更新しました')
        )

