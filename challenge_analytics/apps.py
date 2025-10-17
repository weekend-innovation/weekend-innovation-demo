"""
課題分析アプリの設定
"""
from django.apps import AppConfig


class ChallengeAnalyticsConfig(AppConfig):
    """課題分析アプリの設定"""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'challenge_analytics'
    verbose_name = '課題分析・まとめ機能'
    
    def ready(self):
        """アプリの準備完了時にシグナルを読み込み"""
        import challenge_analytics.signals