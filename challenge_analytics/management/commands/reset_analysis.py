"""
課題分析をリセットして再実行する管理コマンド
"""
from django.core.management.base import BaseCommand
from challenge_analytics.models import ChallengeAnalysis
from challenge_analytics.services import ChallengeAnalyzer


class Command(BaseCommand):
    help = '指定された課題の分析をリセットして再実行します'

    def add_arguments(self, parser):
        parser.add_argument('challenge_id', type=int, help='分析する課題のID')

    def handle(self, *args, **options):
        challenge_id = options['challenge_id']
        
        try:
            # 既存の分析を削除
            deleted_count, _ = ChallengeAnalysis.objects.filter(challenge_id=challenge_id).delete()
            if deleted_count > 0:
                self.stdout.write(self.style.WARNING(f'課題ID {challenge_id} の既存分析を削除しました'))
            
            # 新しいロジックで再分析
            self.stdout.write(self.style.WARNING('\n新しいロジックで分析を実行します...'))
            analyzer = ChallengeAnalyzer(challenge_id)
            analysis = analyzer.analyze_challenge()
            
            self.stdout.write(self.style.SUCCESS('\n✅ 分析完了!'))
            self.stdout.write(f"総提案数: {analysis.total_proposals}")
            self.stdout.write(f"提案者数: {analysis.unique_proposers}")
            self.stdout.write(f"ステータス: {analysis.status}")
            
            # 各提案の洞察を表示
            self.stdout.write(self.style.SUCCESS('\n📊 提案洞察:'))
            for insight in analysis.insights.all():
                self.stdout.write(f"\n提案ID {insight.proposal_id}:")
                self.stdout.write(f"  革新性スコア: {insight.innovation_score:.2f}")
                self.stdout.write(f"  実現可能性スコア: {insight.feasibility_score:.2f}")
                self.stdout.write(f"  影響度スコア: {insight.impact_score:.2f}")
                self.stdout.write(f"  テーマ: {insight.key_themes}")
                self.stdout.write(f"  強み: {insight.strengths}")
                self.stdout.write(f"  懸念点: {insight.concerns}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'エラー: {e}'))
            import traceback
            traceback.print_exc()






