"""
課題分析・まとめ機能のシリアライザー
"""
from rest_framework import serializers
from .models import ChallengeAnalysis, ProposalInsight


class ProposalInsightSerializer(serializers.ModelSerializer):
    """提案洞察のシリアライザー"""
    
    class Meta:
        model = ProposalInsight
        fields = [
            'id',
            'proposal_id',
            'innovation_score',
            'insightfulness_score',
            'impact_score',
            'key_themes',
            'strengths',
            'concerns',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ChallengeAnalysisSerializer(serializers.ModelSerializer):
    """課題分析結果のシリアライザー"""
    
    insights = ProposalInsightSerializer(many=True, read_only=True)
    
    class Meta:
        model = ChallengeAnalysis
        fields = [
            'id',
            'challenge',
            'status',
            'total_proposals',
            'unique_proposers',
            'common_themes',
            'innovative_solutions',
            'feasibility_analysis',
            'executive_summary',
            'detailed_analysis',
            'recommendations',
            'created_at',
            'updated_at',
            'analyzed_at',
            'insights'
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'analyzed_at'
        ]
    
    def to_representation(self, instance):
        """レスポンス形式をカスタマイズ"""
        from proposals.models import Proposal
        from selections.models import Selection
        
        data = super().to_representation(instance)
        
        # 日本語のステータス表示
        status_display = {
            'pending': '分析待ち',
            'processing': '分析中',
            'completed': '完了',
            'failed': '失敗'
        }
        data['status_display'] = status_display.get(instance.status, instance.status)
        
        # 選出されたユーザーのIDリストを取得
        selected_user_ids = set()
        try:
            selection = Selection.objects.filter(challenge=instance.challenge, status='completed').first()
            if selection:
                selected_user_ids = set(selection.selected_users.values_list('id', flat=True))
        except Exception as e:
            print(f"選出ユーザー取得エラー: {e}")
        
        # トップ提案を追加
        insights = instance.insights.all()
        if insights.exists():
            # 独創性トップ
            top_originality = insights.order_by('-innovation_score').first()
            # 支持率トップ
            top_insightfulness = insights.order_by('-insightfulness_score').first()
            # 影響度トップ
            top_impact = insights.order_by('-impact_score').first()
            
            def add_user_attributes(insight_data, proposal_id):
                """提案に属性情報を追加"""
                if not insight_data:
                    return None
                
                try:
                    proposal = Proposal.objects.select_related('proposer', 'proposer__proposer_profile').get(id=proposal_id)
                    if proposal.proposer and proposal.proposer.id in selected_user_ids:
                        insight_data['is_selected'] = True
                        try:
                            profile = proposal.proposer.proposer_profile
                            insight_data['nationality'] = profile.nationality if hasattr(profile, 'nationality') else None
                            insight_data['gender'] = profile.gender if hasattr(profile, 'gender') else None
                            if hasattr(profile, 'birth_date') and profile.birth_date:
                                from datetime import date
                                today = date.today()
                                age = today.year - profile.birth_date.year - ((today.month, today.day) < (profile.birth_date.month, profile.birth_date.day))
                                insight_data['age'] = age
                            else:
                                insight_data['age'] = None
                        except Exception as e:
                            print(f"プロフィール取得エラー: {e}")
                    else:
                        insight_data['is_selected'] = False
                except Exception as e:
                    print(f"提案取得エラー: {e}")
                
                return insight_data
            
            originality_data = ProposalInsightSerializer(top_originality).data if top_originality else None
            insightfulness_data = ProposalInsightSerializer(top_insightfulness).data if top_insightfulness else None
            impact_data = ProposalInsightSerializer(top_impact).data if top_impact else None
            
            data['top_proposals'] = {
                'originality': add_user_attributes(originality_data, top_originality.proposal_id) if top_originality else None,
                'insightfulness': add_user_attributes(insightfulness_data, top_insightfulness.proposal_id) if top_insightfulness else None,
                'impact': add_user_attributes(impact_data, top_impact.proposal_id) if top_impact else None,
            }
        
        return data





