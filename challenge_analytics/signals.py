"""
課題分析のシグナル処理
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from challenges.models import Challenge
from .services import analyze_challenge_on_deadline


@receiver(post_save, sender=Challenge)
def auto_analyze_on_challenge_close(sender, instance, **kwargs):
    """課題が全体として満了（closed／deadline）になった際に自動分析を実行"""
    
    # 課題のステータスがclosedに変更された場合
    if instance.status == 'closed':
        # 既に分析済みでない場合のみ実行
        if not hasattr(instance, 'analysis') or instance.analysis.status != 'completed':
            # 非同期で分析を実行（実際のプロダクションでは Celery などを使用）
            try:
                analyze_challenge_on_deadline(instance.id)
                print(f"課題 {instance.id} の自動分析を開始しました")
            except Exception as e:
                print(f"課題 {instance.id} の自動分析でエラーが発生しました: {e}")






