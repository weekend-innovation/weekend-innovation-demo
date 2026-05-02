"""
モデレーション管理のビュー
"""
import logging
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.db.models import Q, Count
from django.db import transaction

from .models import Report, UserSuspension, ModerationAction
from .serializers import (
    ReportSerializer, ReportCreateSerializer, ReportUpdateSerializer,
    UserSuspensionSerializer, UserSuspensionCreateSerializer,
    ModerationActionSerializer
)
from proposals.models import Proposal, ProposalComment

logger = logging.getLogger(__name__)

User = get_user_model()


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def content_type_lookup(request):
    """Django ContentType の id を app_label + model で返す（通報フォーム用。model は小文字クラス名）。"""
    model = (request.query_params.get("model") or "").strip().lower()
    app_label = (request.query_params.get("app_label") or "proposals").strip().lower()
    if not model:
        return Response({"error": "query parameter model is required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        ct = ContentType.objects.get(app_label=app_label, model=model)
        return Response({"id": ct.id, "app_label": ct.app_label, "model": ct.model})
    except ContentType.DoesNotExist:
        return Response({"error": "ContentType not found"}, status=status.HTTP_404_NOT_FOUND)


class ReportListCreateView(generics.ListCreateAPIView):
    """報告一覧・作成ビュー"""
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ReportCreateSerializer
        return ReportSerializer
    
    def get_queryset(self):
        """クエリセットの取得"""
        queryset = Report.objects.select_related(
            'reporter', 'moderator'
        ).prefetch_related(
            'content_object'
        )
        
        # ユーザーは自分の報告のみ閲覧可能
        if not self.request.user.is_staff:
            queryset = queryset.filter(reporter=self.request.user)
        
        return queryset
    
    def perform_create(self, serializer):
        """報告作成時の処理"""
        # 同じユーザーが同じコンテンツに対して既に報告しているかチェック
        existing_report = Report.objects.filter(
            reporter=self.request.user,
            content_type=serializer.validated_data['content_type'],
            object_id=serializer.validated_data['object_id'],
            status__in=['pending', 'under_review']
        ).exists()
        
        if existing_report:
            raise serializers.ValidationError("このコンテンツは既に報告済みです。")
        
        serializer.save(reporter=self.request.user)


class ReportDetailView(generics.RetrieveUpdateAPIView):
    """報告詳細・更新ビュー"""
    
    serializer_class = ReportUpdateSerializer
    
    def get_queryset(self):
        """クエリセットの取得"""
        queryset = Report.objects.select_related(
            'reporter', 'moderator'
        ).prefetch_related(
            'content_object'
        )
        
        # ユーザーは自分の報告のみ閲覧可能
        if not self.request.user.is_staff:
            queryset = queryset.filter(reporter=self.request.user)
        
        return queryset
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ReportUpdateSerializer
        return ReportSerializer
    
    def perform_update(self, serializer):
        """更新処理"""
        if self.request.user.is_staff:
            # モデレーターの場合のみ更新可能
            serializer.save(moderator=self.request.user)
        else:
            # 一般ユーザーは更新不可
            raise permissions.PermissionDenied("この操作は許可されていません。")


class UserSuspensionListCreateView(generics.ListCreateAPIView):
    """ユーザー利用停止一覧・作成ビュー（管理者のみ）"""
    
    permission_classes = [permissions.IsAdminUser]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserSuspensionCreateSerializer
        return UserSuspensionSerializer
    
    def get_queryset(self):
        """クエリセットの取得"""
        return UserSuspension.objects.select_related(
            'user', 'moderator'
        ).prefetch_related(
            'related_reports'
        )
    
    def perform_create(self, serializer):
        """利用停止作成時の処理"""
        with transaction.atomic():
            # 既存の停止中の停止を解除
            user = serializer.validated_data['user']
            UserSuspension.objects.filter(
                user=user,
                status='active'
            ).update(
                status='lifted',
                lifted_at=timezone.now()
            )
            
            # 新しい停止を作成
            suspension = serializer.save(
                moderator=self.request.user,
                status='active'
            )
            
            # アクション履歴を記録
            ModerationAction.objects.create(
                moderator=self.request.user,
                action_type='user_suspended',
                target_user=user,
                description=f"ユーザー {user.username} を停止しました。理由: {suspension.reason}"
            )


class UserSuspensionDetailView(generics.RetrieveUpdateAPIView):
    """ユーザー利用停止詳細・更新ビュー（管理者のみ）"""
    
    permission_classes = [permissions.IsAdminUser]
    serializer_class = UserSuspensionSerializer
    
    def get_queryset(self):
        """クエリセットの取得"""
        return UserSuspension.objects.select_related(
            'user', 'moderator'
        ).prefetch_related(
            'related_reports'
        )
    
    def perform_update(self, serializer):
        """更新処理"""
        instance = self.get_object()
        
        # 停止解除の場合
        if serializer.validated_data.get('status') == 'lifted':
            serializer.save(
                lifted_at=timezone.now()
            )
            
            # アクション履歴を記録
            ModerationAction.objects.create(
                moderator=self.request.user,
                action_type='user_unsuspended',
                target_user=instance.user,
                description=f"ユーザー {instance.user.username} の停止を解除しました。"
            )
        else:
            serializer.save()


class ModerationActionListView(generics.ListAPIView):
    """モデレーションアクション履歴一覧ビュー（管理者のみ）"""
    
    permission_classes = [permissions.IsAdminUser]
    serializer_class = ModerationActionSerializer
    
    def get_queryset(self):
        """クエリセットの取得"""
        queryset = ModerationAction.objects.select_related(
            'moderator', 'target_user'
        ).prefetch_related(
            'content_object'
        )
        
        # フィルタリング
        action_type = self.request.query_params.get('action_type')
        if action_type:
            queryset = queryset.filter(action_type=action_type)
        
        target_user_id = self.request.query_params.get('target_user')
        if target_user_id:
            queryset = queryset.filter(target_user_id=target_user_id)
        
        return queryset


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_report(request):
    """報告作成API"""
    
    try:
        serializer = ReportCreateSerializer(data=request.data)
    except Exception as e:
        logger.error(f"シリアライザー初期化エラー: {e}", exc_info=True)
        return Response(
            {'error': f'リクエストデータが不正です: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if serializer.is_valid():
        # 同じユーザーが同じコンテンツに対して既に報告しているかチェック
        existing_report = Report.objects.filter(
            reporter=request.user,
            content_type=serializer.validated_data['content_type'],
            object_id=serializer.validated_data['object_id'],
            status__in=['pending', 'under_review']
        ).exists()
        
        if existing_report:
            return Response(
                {'error': 'このコンテンツは既に報告済みです。'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            report = serializer.save(reporter=request.user)
            logger.info(f"通報作成: reporter={request.user.id}, content_type={report.content_type.model}, object_id={report.object_id}")
        except Exception as e:
            logger.error(f"通報保存エラー: {e}", exc_info=True)
            return Response(
                {'error': f'通報の保存に失敗しました: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        try:
            # 同じ課題に選出されたユーザーの10％に報告された場合の処理
            content_model = report.content_type.model
            reported_user = None
            challenge = None
            
            logger.info(f"通報対象コンテンツモデル: {content_model}, object_id={report.object_id}")
            
            # 通報対象のコンテンツとユーザー、課題を特定
            if content_model == 'proposal':
                try:
                    proposal = Proposal.objects.select_related('challenge').get(id=report.object_id)
                    reported_user = proposal.proposer
                    challenge = proposal.challenge
                    logger.info(f"Proposal通報: reported_user={reported_user.username}, challenge={challenge.id}")
                except Proposal.DoesNotExist:
                    logger.warning(f"Proposal not found: id={report.object_id}")
            
            elif content_model == 'proposalcomment':
                try:
                    comment = ProposalComment.objects.select_related('proposal__challenge', 'commenter').get(id=report.object_id)
                    reported_user = comment.commenter
                    challenge = comment.proposal.challenge
                    logger.info(f"ProposalComment通報: reported_user={reported_user.username}, challenge={challenge.id}")
                except ProposalComment.DoesNotExist:
                    logger.warning(f"ProposalComment not found: id={report.object_id}")
            
            elif content_model == 'proposalcommentreply':
                try:
                    from proposals.models import ProposalCommentReply
                    reply = ProposalCommentReply.objects.select_related('comment__proposal__challenge', 'replier').get(id=report.object_id)
                    reported_user = reply.replier
                    challenge = reply.comment.proposal.challenge
                    logger.info(f"ProposalCommentReply通報: reported_user={reported_user.username}, challenge={challenge.id}")
                except ProposalCommentReply.DoesNotExist:
                    logger.warning(f"ProposalCommentReply not found: id={report.object_id}")
            
            # 通報対象ユーザーと課題が特定できた場合のみ処理
            if reported_user and challenge:
                # その課題に選出されたユーザー数を取得
                from selections.models import Selection
                
                selected_users_count = Selection.objects.filter(
                    challenge=challenge
                ).aggregate(
                    total=Count('selected_users', distinct=True)
                )['total'] or 0
                
                if selected_users_count > 0:
                    # このコンテンツに対する通報数を取得（重複通報を除外）
                    report_count = Report.objects.filter(
                        content_type=report.content_type,
                        object_id=report.object_id,
                        status__in=['pending', 'under_review']
                    ).values('reporter').distinct().count()
                    
                    # 選出ユーザーの10％以上が通報した場合
                    threshold = max(1, int(selected_users_count * 0.1))
                    
                    if report_count >= threshold:
                        # 既に停止中でないか確認
                        existing_suspension = UserSuspension.objects.filter(
                            user=reported_user,
                            status='active',
                            suspended_until__gt=timezone.now()
                        ).exists()
                        
                        if not existing_suspension:
                            # 3か月（90日）の停止
                            suspension_until = timezone.now() + timezone.timedelta(days=90)
                            
                            UserSuspension.objects.create(
                                user=reported_user,
                                reason='multiple_violations',
                                description=f'課題「{challenge.title}」において、選出されたユーザーの10％以上から通報されました。自動停止。',
                                suspended_until=suspension_until,
                                moderator=None  # システムによる自動停止
                            )
                            
                            # アクション履歴を記録
                            ModerationAction.objects.create(
                                moderator=None,  # システムによる自動処理
                                action_type='user_suspended',
                                target_user=reported_user,
                                description=f'ユーザー {reported_user.username} を自動停止しました。課題「{challenge.title}」の選出ユーザーの10％以上（{report_count}/{selected_users_count}人）から通報されました。'
                            )
        except Exception as e:
            logger.error(f"通報処理エラー: {e}", exc_info=True)
            # エラーが発生しても通報自体は保存されているので成功レスポンスを返す
        
        return Response(
            ReportSerializer(report).data,
            status=status.HTTP_201_CREATED
        )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def check_if_reported(request):
    """ユーザーが特定のコンテンツを報告済みかどうかを確認"""
    content_type_id = request.query_params.get('content_type')
    object_id = request.query_params.get('object_id')
    
    if not content_type_id or not object_id:
        return Response(
            {'error': 'content_typeとobject_idが必要です。'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        object_id_int = int(object_id)
        content_type_int = int(content_type_id)
        is_reported = Report.objects.filter(
            reporter=request.user,
            content_type_id=content_type_int,
            object_id=object_id_int,
            status__in=['pending', 'under_review'],
        ).exists()
        
        return Response({'is_reported': is_reported})
    except Exception as e:
        logger.error(f"報告済み確認エラー: {e}", exc_info=True)
        return Response(
            {'error': '確認に失敗しました。'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def report_stats(request):
    """報告統計情報取得API"""
    
    if not request.user.is_staff:
        return Response(
            {'error': 'この操作は許可されていません。'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    stats = {
        'total_reports': Report.objects.count(),
        'pending_reports': Report.objects.filter(status='pending').count(),
        'under_review_reports': Report.objects.filter(status='under_review').count(),
        'resolved_reports': Report.objects.filter(status='resolved').count(),
        'active_suspensions': UserSuspension.objects.filter(status='active').count(),
        'reports_by_reason': dict(
            Report.objects.values('reason').annotate(
                count=Count('id')
            ).values_list('reason', 'count')
        ),
        'reports_by_content_type': dict(
            Report.objects.values('content_type__model').annotate(
                count=Count('id')
            ).values_list('content_type__model', 'count')
        ),
    }
    
    return Response(stats)


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def bulk_moderate_reports(request):
    """報告の一括モデレーションAPI"""
    
    report_ids = request.data.get('report_ids', [])
    action = request.data.get('action')  # 'approve', 'dismiss', 'resolve'
    moderator_notes = request.data.get('moderator_notes', '')
    
    if not report_ids or not action:
        return Response(
            {'error': 'report_ids と action が必要です。'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if action not in ['approve', 'dismiss', 'resolve']:
        return Response(
            {'error': 'action は approve, dismiss, resolve のいずれかである必要があります。'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    reports = Report.objects.filter(
        id__in=report_ids,
        status__in=['pending', 'under_review']
    )
    
    updated_reports = []
    
    with transaction.atomic():
        for report in reports:
            if action == 'approve':
                report.status = 'under_review'
            elif action == 'dismiss':
                report.status = 'dismissed'
            elif action == 'resolve':
                report.status = 'resolved'
                report.resolved_at = timezone.now()
            
            report.moderator = request.user
            report.moderator_notes = moderator_notes
            report.save()
            updated_reports.append(report)
    
    return Response({
        'message': f'{len(updated_reports)}件の報告を{action}しました。',
        'updated_reports': [report.id for report in updated_reports]
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_suspension_status(request):
    """ユーザーの停止状況取得API"""
    
    user = request.user
    
    # 現在有効な停止を取得
    active_suspension = UserSuspension.objects.filter(
        user=user,
        status='active',
        suspended_until__gt=timezone.now()
    ).first()
    
    if active_suspension:
        return Response({
            'is_suspended': True,
            'suspension': UserSuspensionSerializer(active_suspension).data
        })
    else:
        return Response({
            'is_suspended': False,
            'suspension': None
        })