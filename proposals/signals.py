"""
提案関連のシグナル処理
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Avg, Count
from .models import Proposal, ProposalEvaluation
from payments.models import Payment, PaymentHistory


@receiver(post_save, sender=Proposal)
def create_proposal_payment(sender, instance, created, **kwargs):
    """提案作成時に自動で提案報酬を支払う"""
    if created and instance.challenge:
        challenge = instance.challenge
        
        # 提案報酬が設定されている場合のみ支払い処理
        if challenge.reward_amount and challenge.reward_amount > 0:
            try:
                # 支払い記録を作成
                payment = Payment.objects.create(
                    payer=challenge.contributor,
                    recipient=instance.proposer,
                    amount=challenge.reward_amount,
                    payment_type='proposal_reward',
                    status='pending',
                    challenge=challenge,
                    proposal=instance,
                    description=f'課題「{challenge.title}」への提案報酬'
                )
                
                # 支払い処理を実行
                payment.process_payment()
                
                # 履歴記録
                PaymentHistory.objects.create(
                    payment=payment,
                    action='auto_payment_created',
                    details=f'提案作成による自動報酬支払い: ¥{challenge.reward_amount}'
                )
                
            except Exception as e:
                # エラーが発生した場合は失敗ステータスに設定
                payment.status = 'failed'
                payment.save()
                
                PaymentHistory.objects.create(
                    payment=payment,
                    action='auto_payment_failed',
                    details=f'自動報酬支払い失敗: {str(e)}'
                )


@receiver(post_save, sender=Proposal)
def create_adoption_payment(sender, instance, created, **kwargs):
    """提案が採用された時に自動で採用報酬を支払う"""
    # 採用状態が変更された場合のみ処理
    if not created and instance.is_adopted and instance.challenge:
        challenge = instance.challenge
        
        # 採用報酬が設定されている場合のみ支払い処理
        if challenge.adoption_reward and challenge.adoption_reward > 0:
            try:
                # 既存の採用報酬支払いがないかチェック
                existing_payment = Payment.objects.filter(
                    payer=challenge.contributor,
                    recipient=instance.proposer,
                    proposal=instance,
                    payment_type='adoption_reward'
                ).exists()
                
                if not existing_payment:
                    # 支払い記録を作成
                    payment = Payment.objects.create(
                        payer=challenge.contributor,
                        recipient=instance.proposer,
                        amount=challenge.adoption_reward,
                        payment_type='adoption_reward',
                        status='pending',
                        challenge=challenge,
                        proposal=instance,
                        description=f'課題「{challenge.title}」の提案採用報酬'
                    )
                    
                    # 支払い処理を実行
                    payment.process_payment()
                    
                    # 履歴記録
                    PaymentHistory.objects.create(
                        payment=payment,
                        action='auto_adoption_payment_created',
                        details=f'提案採用による自動報酬支払い: ¥{challenge.adoption_reward}'
                    )
                
            except Exception as e:
                # エラーが発生した場合は失敗ステータスに設定
                if 'payment' in locals():
                    payment.status = 'failed'
                    payment.save()
                    
                    PaymentHistory.objects.create(
                        payment=payment,
                        action='auto_adoption_payment_failed',
                        details=f'自動採用報酬支払い失敗: {str(e)}'
                    )


@receiver(post_save, sender=ProposalEvaluation)
@receiver(post_delete, sender=ProposalEvaluation)
def update_proposal_rating(sender, instance, **kwargs):
    """評価が作成・削除されたときに提案のratingとrating_countを更新"""
    try:
        proposal = instance.proposal
        
        # 評価の集計
        evaluations = ProposalEvaluation.objects.filter(proposal=proposal)
        rating_count = evaluations.count()
        
        if rating_count > 0:
            # 平均スコアを計算
            avg_score = evaluations.aggregate(Avg('score'))['score__avg']
            proposal.rating = avg_score
            proposal.rating_count = rating_count
        else:
            proposal.rating = None
            proposal.rating_count = 0
        
        proposal.save(update_fields=['rating', 'rating_count'])
        
    except Exception as e:
        pass
