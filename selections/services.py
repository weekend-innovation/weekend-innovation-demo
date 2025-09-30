"""
選出機能のサービス層
ランダム選出ロジックと選出管理機能を提供
"""
import random
import logging
from typing import List, Dict, Any, Optional
from django.db import transaction, models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError

from .models import Selection, SelectionHistory, SelectionCriteria
from .notifications import SelectionNotificationService
from challenges.models import Challenge
from proposals.models import Proposal

User = get_user_model()
logger = logging.getLogger(__name__)


class SelectionService:
    """
    選出サービスクラス
    選出に関するビジネスロジックを管理
    """
    
    @staticmethod
    def create_selection(challenge: Challenge, required_count: int, 
                        selection_criteria: Optional[Dict[str, Any]] = None) -> Selection:
        """
        選出を作成
        
        Args:
            challenge: 対象の課題
            required_count: 選出人数
            selection_criteria: 選出基準
            
        Returns:
            Selection: 作成された選出オブジェクト
        """
        try:
            with transaction.atomic():
                selection = Selection.objects.create(
                    challenge=challenge,
                    contributor=challenge.contributor,
                    required_count=required_count,
                    selection_criteria=selection_criteria or {},
                    status='pending'
                )
                
                logger.info(f"選出を作成しました: {selection.id}")
                return selection
                
        except Exception as e:
            logger.error(f"選出作成エラー: {e}")
            raise ValidationError(f"選出の作成に失敗しました: {str(e)}")
    
    @staticmethod
    def get_eligible_users(challenge: Challenge, criteria: Optional[Dict[str, Any]] = None) -> List[User]:
        """
        選出対象となるユーザーを取得
        
        Args:
            challenge: 対象の課題
            criteria: 選出基準
            
        Returns:
            List[User]: 選出対象ユーザーのリスト
        """
        try:
            # 基本的なフィルタリング条件
            queryset = User.objects.filter(
                user_type='proposer',
                is_active=True
            ).exclude(
                id=challenge.contributor.id  # 投稿者本人は除外
            )
            
            # 提案履歴によるフィルタリング（オプション）
            if criteria and criteria.get('require_proposal_history', False):
                # 提案履歴があるユーザーのみ
                queryset = queryset.filter(
                    proposals__isnull=False
                ).distinct()
            
            # 評価基準によるフィルタリング（オプション）
            if criteria and criteria.get('min_rating', 0) > 0:
                # 最低評価値以上のユーザーのみ
                queryset = queryset.filter(
                    proposer_profile__rating__gte=criteria['min_rating']
                )
            
            # 地域によるフィルタリング（オプション）
            if criteria and criteria.get('location_filter'):
                location = criteria['location_filter']
                queryset = queryset.filter(
                    proposer_profile__address__icontains=location
                )
            
            eligible_users = list(queryset)
            logger.info(f"選出対象ユーザー数: {len(eligible_users)}")
            
            return eligible_users
            
        except Exception as e:
            logger.error(f"選出対象ユーザー取得エラー: {e}")
            return []
    
    @staticmethod
    def random_selection(challenge: Challenge, required_count: int, 
                        criteria: Optional[Dict[str, Any]] = None) -> Selection:
        """
        ランダム選出を実行
        
        Args:
            challenge: 対象の課題
            required_count: 選出人数
            criteria: 選出基準
            
        Returns:
            Selection: 選出結果
        """
        try:
            with transaction.atomic():
                # 選出対象ユーザーを取得
                eligible_users = SelectionService.get_eligible_users(challenge, criteria)
                
                if not eligible_users:
                    raise ValidationError("選出対象となるユーザーが存在しません")
                
                if len(eligible_users) < required_count:
                    logger.warning(f"選出対象ユーザー数({len(eligible_users)})が要求人数({required_count})より少ない")
                    required_count = len(eligible_users)
                
                # ランダム選出実行
                selected_users = random.sample(eligible_users, required_count)
                
                # 選出オブジェクトを作成
                selection = SelectionService.create_selection(
                    challenge=challenge,
                    required_count=required_count,
                    selection_criteria=criteria
                )
                
                # 選出されたユーザーを登録
                selection.selected_users.set(selected_users)
                selection.selected_count = len(selected_users)
                selection.status = 'completed'
                selection.completed_at = timezone.now()
                selection.save()
                
                # 選出履歴を記録
                for user in selected_users:
                    SelectionHistory.objects.create(
                        selection=selection,
                        user=user,
                        action='selected',
                        reason='ランダム選出',
                        metadata={
                            'selection_method': 'random',
                            'challenge_id': challenge.id,
                            'criteria': criteria or {}
                        }
                    )
                
                logger.info(f"ランダム選出完了: {selection.id}, 選出人数: {len(selected_users)}")
                
                # 通知を送信
                SelectionNotificationService.send_selection_notification(selection)
                
                return selection
                
        except Exception as e:
            logger.error(f"ランダム選出エラー: {e}")
            raise ValidationError(f"ランダム選出に失敗しました: {str(e)}")
    
    @staticmethod
    def weighted_selection(challenge: Challenge, required_count: int,
                          criteria: Optional[Dict[str, Any]] = None) -> Selection:
        """
        重み付き選出を実行（評価や経験値に基づく）
        
        Args:
            challenge: 対象の課題
            required_count: 選出人数
            criteria: 選出基準
            
        Returns:
            Selection: 選出結果
        """
        try:
            with transaction.atomic():
                # 選出対象ユーザーを取得
                eligible_users = SelectionService.get_eligible_users(challenge, criteria)
                
                if not eligible_users:
                    raise ValidationError("選出対象となるユーザーが存在しません")
                
                if len(eligible_users) < required_count:
                    required_count = len(eligible_users)
                
                # 重み計算
                user_weights = []
                for user in eligible_users:
                    weight = SelectionService._calculate_user_weight(user, criteria)
                    user_weights.append((user, weight))
                
                # 重みに基づく選出
                selected_users = SelectionService._weighted_random_choice(
                    user_weights, required_count
                )
                
                # 選出オブジェクトを作成
                selection = SelectionService.create_selection(
                    challenge=challenge,
                    required_count=required_count,
                    selection_criteria=criteria
                )
                
                # 選出されたユーザーを登録
                selection.selected_users.set(selected_users)
                selection.selected_count = len(selected_users)
                selection.status = 'completed'
                selection.completed_at = timezone.now()
                selection.save()
                
                # 選出履歴を記録
                for user in selected_users:
                    SelectionHistory.objects.create(
                        selection=selection,
                        user=user,
                        action='selected',
                        reason='重み付き選出',
                        metadata={
                            'selection_method': 'weighted',
                            'challenge_id': challenge.id,
                            'criteria': criteria or {}
                        }
                    )
                
                logger.info(f"重み付き選出完了: {selection.id}, 選出人数: {len(selected_users)}")
                
                # 通知を送信
                SelectionNotificationService.send_selection_notification(selection)
                
                return selection
                
        except Exception as e:
            logger.error(f"重み付き選出エラー: {e}")
            raise ValidationError(f"重み付き選出に失敗しました: {str(e)}")
    
    @staticmethod
    def _calculate_user_weight(user: User, criteria: Optional[Dict[str, Any]] = None) -> float:
        """
        ユーザーの重みを計算
        
        Args:
            user: 対象ユーザー
            criteria: 選出基準
            
        Returns:
            float: ユーザーの重み
        """
        weight = 1.0
        
        try:
            # 評価値による重み調整
            if hasattr(user, 'proposer_profile') and user.proposer_profile.rating:
                weight *= (1 + user.proposer_profile.rating / 10.0)
            
            # 提案履歴による重み調整
            proposal_count = Proposal.objects.filter(proposer=user).count()
            weight *= (1 + proposal_count * 0.1)
            
            # 採用率による重み調整
            adopted_count = Proposal.objects.filter(proposer=user, is_adopted=True).count()
            if proposal_count > 0:
                adoption_rate = adopted_count / proposal_count
                weight *= (1 + adoption_rate * 0.5)
            
            # 基準による重み調整
            if criteria:
                if criteria.get('prefer_experienced', False):
                    # 経験豊富なユーザーを優先
                    weight *= (1 + proposal_count * 0.05)
                
                if criteria.get('location_bonus', False) and hasattr(user, 'proposer_profile'):
                    # 特定地域のユーザーにボーナス
                    preferred_location = criteria.get('preferred_location', '')
                    if preferred_location in user.proposer_profile.address:
                        weight *= 1.2
            
        except Exception as e:
            logger.warning(f"ユーザー重み計算エラー (user_id: {user.id}): {e}")
            weight = 1.0
        
        return max(0.1, weight)  # 最小重みを0.1に設定
    
    @staticmethod
    def _weighted_random_choice(user_weights: List[tuple], count: int) -> List[User]:
        """
        重み付きランダム選択
        
        Args:
            user_weights: (ユーザー, 重み)のタプルのリスト
            count: 選出人数
            
        Returns:
            List[User]: 選出されたユーザーのリスト
        """
        if not user_weights or count <= 0:
            return []
        
        if len(user_weights) <= count:
            return [user for user, _ in user_weights]
        
        selected_users = []
        remaining_weights = user_weights.copy()
        
        for _ in range(count):
            if not remaining_weights:
                break
            
            # 重みの合計を計算
            total_weight = sum(weight for _, weight in remaining_weights)
            
            # ランダム値を生成
            random_value = random.uniform(0, total_weight)
            
            # 重みに基づいてユーザーを選択
            cumulative_weight = 0
            for i, (user, weight) in enumerate(remaining_weights):
                cumulative_weight += weight
                if random_value <= cumulative_weight:
                    selected_users.append(user)
                    remaining_weights.pop(i)
                    break
        
        return selected_users
    
    @staticmethod
    def cancel_selection(selection: Selection, reason: str = "") -> bool:
        """
        選出をキャンセル
        
        Args:
            selection: 対象の選出
            reason: キャンセル理由
            
        Returns:
            bool: キャンセル成功フラグ
        """
        try:
            with transaction.atomic():
                selection.status = 'cancelled'
                selection.save()
                
                # 履歴を記録
                SelectionHistory.objects.create(
                    selection=selection,
                    user=selection.contributor,
                    action='removed',
                    reason=f'選出キャンセル: {reason}',
                    metadata={
                        'cancelled_by': 'contributor',
                        'reason': reason
                    }
                )
                
                logger.info(f"選出をキャンセルしました: {selection.id}")
                return True
                
        except Exception as e:
            logger.error(f"選出キャンセルエラー: {e}")
            return False
    
    @staticmethod
    def get_selection_statistics() -> Dict[str, Any]:
        """
        選出統計を取得
        
        Returns:
            Dict[str, Any]: 統計情報
        """
        try:
            total_selections = Selection.objects.count()
            completed_selections = Selection.objects.filter(status='completed').count()
            pending_selections = Selection.objects.filter(status='pending').count()
            cancelled_selections = Selection.objects.filter(status='cancelled').count()
            
            total_selected_users = Selection.objects.aggregate(
                total=models.Sum('selected_count')
            )['total'] or 0
            
            avg_selection_size = Selection.objects.filter(
                status='completed'
            ).aggregate(
                avg=models.Avg('selected_count')
            )['avg'] or 0
            
            return {
                'total_selections': total_selections,
                'completed_selections': completed_selections,
                'pending_selections': pending_selections,
                'cancelled_selections': cancelled_selections,
                'total_selected_users': total_selected_users,
                'average_selection_size': round(avg_selection_size, 2),
                'completion_rate': round(
                    (completed_selections / total_selections * 100) if total_selections > 0 else 0, 2
                )
            }
            
        except Exception as e:
            logger.error(f"統計取得エラー: {e}")
            return {}
