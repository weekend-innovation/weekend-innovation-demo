"""
全提案の評価を集計して更新する管理コマンド
"""
from django.core.management.base import BaseCommand
from django.db.models import Avg, Count
from proposals.models import Proposal, ProposalEvaluation


class Command(BaseCommand):
    help = '全ての提案の評価を集計してratingとrating_countを更新します'

    def handle(self, *args, **options):
        proposals = Proposal.objects.all()
        updated_count = 0
        
        for proposal in proposals:
            evaluations = ProposalEvaluation.objects.filter(proposal=proposal)
            rating_count = evaluations.count()
            
            if rating_count > 0:
                avg_score = evaluations.aggregate(Avg('score'))['score__avg']
                proposal.rating = avg_score
                proposal.rating_count = rating_count
                self.stdout.write(f"提案ID {proposal.id}: rating={avg_score}, rating_count={rating_count}")
                updated_count += 1
            else:
                proposal.rating = None
                proposal.rating_count = 0
            
            proposal.save(update_fields=['rating', 'rating_count'])
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ {updated_count}件の提案の評価を更新しました！'))






