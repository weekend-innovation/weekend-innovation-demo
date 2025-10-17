import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mvp_project.settings')
django.setup()

from django.db.models import Avg, Count
from proposals.models import Proposal, ProposalEvaluation

# すべての提案について評価を集計
proposals = Proposal.objects.all()

for proposal in proposals:
    evaluations = ProposalEvaluation.objects.filter(proposal=proposal)
    rating_count = evaluations.count()
    
    if rating_count > 0:
        avg_score = evaluations.aggregate(Avg('score'))['score__avg']
        proposal.rating = avg_score
        proposal.rating_count = rating_count
        print(f"提案ID {proposal.id}: rating={avg_score}, rating_count={rating_count}")
    else:
        proposal.rating = None
        proposal.rating_count = 0
        print(f"提案ID {proposal.id}: 評価なし")
    
    proposal.save(update_fields=['rating', 'rating_count'])

print("\n✅ 全ての提案の評価を更新しました！")






