/**
 * 提案コメント一覧コンポーネント
 * コメント表示、返信機能を含む
 */
import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import ProposalCommentReplyForm from './ProposalCommentReplyForm';
import ProposalCommentForm from './ProposalCommentForm';
import ProposalEditForm from './ProposalEditForm';
import { ReportButton } from '../moderation/ReportButton';
import type {
  ProposalCommentListProps,
  CreateProposalCommentRequest,
  CreateProposalCommentReplyRequest,
} from '../../types/proposal';

const ProposalCommentList: React.FC<ProposalCommentListProps> = ({
  proposalId,
  proposal,
  proposalState,
  comments,
  onAddComment,
  onReply,
  onEdit,
  onReference,
  isAddingComment = false,
  isReplying = false,
  isEditing = false,
  editingCommentId = null,
  setEditingCommentId,
  canComment = false,
  canReply = false,
  canReference = false
}) => {
  void proposalId;
  void onReference;
  const { user } = useAuth();
  const [replyingCommentId, setReplyingCommentId] = useState<number | null>(null);

  const isCurrentUserComment = (comment: { commenter?: number; commenter_name: string }) => {
    if (!user) return false;
    if (comment.commenter != null) {
      return comment.commenter === Number(user.id);
    }
    return comment.commenter_name === user.username;
  };

  const isCurrentUserReply = (reply: { replier?: number; replier_name: string }) => {
    if (!user) return false;
    if (reply.replier != null) {
      return reply.replier === Number(user.id);
    }
    return reply.replier_name === user.username;
  };

  const handleAddComment = (comment: CreateProposalCommentRequest) => {
    onAddComment(comment);
  };

  const handleReply = (commentId: number, reply: CreateProposalCommentReplyRequest) => {
    onReply(commentId, reply);
    setReplyingCommentId(null);
  };

  const handleStartReply = (commentId: number) => {
    setReplyingCommentId(commentId);
  };

  const handleCancelReply = () => {
    setReplyingCommentId(null);
  };

  // 参考ハンドラー（解決案編集機能）
  const handleReference = (commentId: number) => {
    if (setEditingCommentId) {
      setEditingCommentId(commentId);
    }
  };

  const handleCancelEdit = () => {
    if (setEditingCommentId) {
      setEditingCommentId(null);
    }
  };

  const handleEdit = (
    proposalId: number,
    data: { conclusion: string; reasoning: string },
    referenceCommentId?: number | null
  ) => {
    onEdit(proposalId, data, referenceCommentId);
  };

  const getTargetSectionLabel = (targetSection: 'reasoning' | 'inference') => {
    switch (targetSection) {
      case 'reasoning':
        return '理由';
      case 'inference':
        return '推論過程';
      default:
        return targetSection;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ja-JP', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="space-y-4">
      {/* コメント一覧 */}
      {comments.length > 0 ? (
        <div className="space-y-3">
          <h4 className="font-medium text-gray-900">コメント一覧 ({comments.length}件)</h4>
          
          {comments.map((comment) => (
            <div key={comment.id} className="bg-white border rounded-lg p-4">
              {/* コメントヘッダー */}
              <div className="flex justify-between items-start mb-3">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-gray-900">{comment.commenter_name}</span>
                  <span className={`text-xs px-2 py-1 rounded ${
                    comment.target_section === 'reasoning' 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-pink-100 text-pink-800'
                  }`}>
                    {getTargetSectionLabel(comment.target_section)}へのコメント
                  </span>
                </div>
                <span className="text-sm text-gray-500">
                  {formatDate(comment.created_at)}
                </span>
              </div>

              {/* コメント内容 */}
              <div className="space-y-3">
                <div>
                  <h5 className="font-medium text-gray-700 mb-1">【結論】</h5>
                  <div className="bg-pink-50 rounded-lg p-3">
                    <p className="text-gray-600 text-sm leading-relaxed">{comment.conclusion}</p>
                  </div>
                </div>
                
                <div>
                  <h5 className="font-medium text-gray-700 mb-1">【理由】</h5>
                  <div className="bg-green-50 rounded-lg p-3">
                    <p className="text-gray-600 text-sm leading-relaxed">{comment.reasoning}</p>
                  </div>
                </div>
              </div>

              {/* アクションボタン */}
              {canReply && user && (
                <div className="mt-3 pt-3 border-t border-gray-200">
                  {replyingCommentId === comment.id ? (
                    <ProposalCommentReplyForm
                      commentId={comment.id}
                      onSubmit={(reply) => handleReply(comment.id, reply)}
                      onCancel={handleCancelReply}
                      isLoading={isReplying}
                    />
                  ) : editingCommentId === comment.id ? (
                    canReference ? (
                      <ProposalEditForm
                        proposal={proposalState || proposal}
                        referenceCommentId={comment.id}
                        onSubmit={(proposalId, data) =>
                          handleEdit(proposalId, data, comment.id)
                        }
                        onCancel={handleCancelEdit}
                        isLoading={isEditing}
                      />
                    ) : (
                      <div className="mt-2 flex flex-col items-end gap-2">
                        <p className="text-sm text-amber-800 text-right max-w-md">
                          編集期間のみ「参考」による解決案の保存ができます。提案期間中はコメントへの返信のみ利用できます。
                        </p>
                        <button
                          type="button"
                          onClick={handleCancelEdit}
                          className="bg-gray-200 text-gray-800 px-4 py-2 rounded-lg hover:bg-gray-300 text-sm font-medium cursor-pointer"
                        >
                          閉じる
                        </button>
                      </div>
                    )
                  ) : (
                    <div className="flex justify-end gap-2">
                      <button
                        onClick={() => handleStartReply(comment.id)}
                        className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors duration-200 text-sm font-medium shadow-sm hover:shadow-md cursor-pointer"
                      >
                        返信
                      </button>
                      {canReference && (
                        <button
                          onClick={() => handleReference(comment.id)}
                          className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors duration-200 text-sm font-medium shadow-sm hover:shadow-md cursor-pointer"
                        >
                          参考
                        </button>
                      )}
                      {/* 自分の解決案に対するコメントの通報ボタン（自分のコメント以外） */}
                      {!isCurrentUserComment(comment) && (
                        <ReportButton
                          contentTypeModel="proposalcomment"
                          objectId={comment.id}
                          contentTypeName="コメント"
                          size="sm"
                          className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors duration-200 text-sm font-medium shadow-sm hover:shadow-md cursor-pointer"
                        />
                      )}
                    </div>
                  )}
                </div>
              )}
              
              {/* 他のユーザーの解決案に対するコメントの通報ボタン（自分のコメント以外） */}
              {!canReply && canComment && user && !isCurrentUserComment(comment) && (
                <div className="mt-3 pt-3 border-t border-gray-200">
                  <div className="flex justify-end">
                    <ReportButton
                      contentTypeModel="proposalcomment"
                      objectId={comment.id}
                      contentTypeName="コメント"
                      size="sm"
                      className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors duration-200 text-sm font-medium shadow-sm hover:shadow-md cursor-pointer"
                    />
                  </div>
                </div>
              )}

              {/* 返信セクション */}
              {comment.replies && comment.replies.length > 0 && (
                <div className="mt-4 space-y-2">
                  <h6 className="font-medium text-gray-700 text-sm">返信:</h6>
                  {comment.replies.map((reply) => (
                    <div key={reply.id} className="bg-blue-50 rounded p-3 border border-blue-100">
                      <div className="flex justify-between items-start mb-2">
                        <span className="font-medium text-gray-800 text-sm">{reply.replier_name}</span>
                        <span className="text-xs text-gray-500">{formatDate(reply.created_at)}</span>
                      </div>
                      <p className="text-gray-600 text-sm leading-relaxed">{reply.content}</p>
                      
                      {/* 返信の通報ボタン（自分の返信以外） */}
                      {user && !isCurrentUserReply(reply) && (
                        <div className="mt-2 pt-2 border-t border-gray-200">
                          <div className="flex justify-end">
                            <ReportButton
                              contentTypeModel="proposalcommentreply"
                              objectId={reply.id}
                              contentTypeName="返信"
                              size="sm"
                              className="bg-red-600 text-white px-3 py-1 rounded-md hover:bg-red-700 transition-colors duration-200 text-xs font-medium shadow-sm hover:shadow-md cursor-pointer"
                            />
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-4">
          <p className="text-gray-500 text-sm">まだコメントがありません。</p>
        </div>
      )}

      {/* コメント追加セクション */}
      {canComment && (
        <ProposalCommentForm
          onSubmit={handleAddComment}
          isLoading={isAddingComment}
        />
      )}

    </div>
  );
};

export default ProposalCommentList;
