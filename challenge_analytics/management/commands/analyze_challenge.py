"""
課題分析を実行する管理コマンド
"""
from django.core.management.base import BaseCommand
from challenge_analytics.services import ChallengeAnalyzer
from challenges.models import Challenge


class Command(BaseCommand):
    help = '指定された課題の分析を実行します'

    def add_arguments(self, parser):
        parser.add_argument('challenge_id', type=int, help='分析する課題のID')

    def handle(self, *args, **options):
        challenge_id = options['challenge_id']
        
        try:
            challenge = Challenge.objects.get(id=challenge_id)
            self.stdout.write(f"課題: {challenge.title}")
            self.stdout.write(f"ステータス: {challenge.status}")
            self.stdout.write(f"期限: {challenge.deadline}")
            
            self.stdout.write(self.style.WARNING('\n分析を開始します...'))
            analyzer = ChallengeAnalyzer(challenge_id)
            analysis = analyzer.analyze_challenge()
            
            self.stdout.write(self.style.SUCCESS('\n分析完了!'))
            self.stdout.write(f"総提案数: {analysis.total_proposals}")
            self.stdout.write(f"提案者数: {analysis.unique_proposers}")
            self.stdout.write(f"ステータス: {analysis.status}")
            self.stdout.write(f"\nエグゼクティブサマリー:")
            self.stdout.write(analysis.executive_summary[:300] + "...")
            
        except Challenge.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'課題ID {challenge_id} が見つかりません'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'エラー: {e}'))
            import traceback
            traceback.print_exc()






