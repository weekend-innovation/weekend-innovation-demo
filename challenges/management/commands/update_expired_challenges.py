"""
期限切れ課題のステータスを自動更新する管理コマンド
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from challenges.models import Challenge


class Command(BaseCommand):
    help = '期限切れの課題を自動的にclosedステータスに更新します'

    def handle(self, *args, **options):
        """コマンド実行処理"""
        now = timezone.now()
        
        # 期限切れでまだopenステータスの課題を取得
        expired_challenges = Challenge.objects.filter(
            status='open',
            deadline__lt=now
        )
        
        count = expired_challenges.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('期限切れの課題はありません'))
            return
        
        # ステータスを'closed'に更新
        expired_challenges.update(status='closed')
        
        self.stdout.write(
            self.style.SUCCESS(f'{count}件の課題を期限切れ(closed)に更新しました')
        )
        
        # 更新された課題の詳細を表示
        for challenge in expired_challenges:
            self.stdout.write(
                f'  - {challenge.title} (ID: {challenge.id}, 期限: {challenge.deadline})'
            )


