/**
 * 提案カードコンポーネント
 * 提案一覧での表示用
 */
import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useAuth } from '../../contexts/AuthContext';
import ProposalEvaluationComponent from './ProposalEvaluation';
import ProposalCommentList from './ProposalCommentList';
import { createProposalEvaluation, createProposalComment, createProposalCommentReply, getProposalComments, getProposalEvaluation } from '../../lib/proposalAPI';
import type { ProposalListItem, ProposalCardProps, ProposalComment, ProposalEvaluation, ReferenceLog } from '@/types/proposal';

const ProposalCard: React.FC<ProposalCardProps> = ({
  proposal,
  showActions = false,
  showEditDelete = true,
  showStatus = true,
  showComments = false,
  showChallengeInfo = true,
  challengeId,
  onView,
  onEdit,
  onDelete,
  onAdopt,
  onComments
}) => {
  const { user } = useAuth();
  const [showCommentsSection, setShowCommentsSection] = useState(false);
  const [comments, setComments] = useState<ProposalComment[]>([]);
  const [userEvaluation, setUserEvaluation] = useState<ProposalEvaluation | null>(null);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [isAddingComment, setIsAddingComment] = useState(false);
  const [isReplying, setIsReplying] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [unreadCount, setUnreadCount] = useState(proposal.unread_comment_count || 0);
  const [referenceLogs, setReferenceLogs] = useState<ReferenceLog[]>([]);
  const [editingCommentId, setEditingCommentId] = useState<number | null>(null);
  const [proposalState, setProposalState] = useState(proposal);

  // localStorageから参考ログと編集された解決案を読み込み
  useEffect(() => {
    const savedLogs = localStorage.getItem(`referenceLogs_${proposal.id}`);
    if (savedLogs) {
      try {
        const logs = JSON.parse(savedLogs);
        setReferenceLogs(logs);
      } catch (error) {
        console.error('Failed to parse reference logs:', error);
      }
    }

    const savedProposal = localStorage.getItem(`editedProposal_${proposal.id}`);
    if (savedProposal) {
      try {
        const editedData = JSON.parse(savedProposal);
        setProposalState(prev => ({
          ...prev,
          conclusion: editedData.conclusion,
          reasoning: editedData.reasoning
        }));
      } catch (error) {
        console.error('Failed to parse edited proposal:', error);
      }
    }
  }, [proposal.id]);

  // 参考ログが変更されたらlocalStorageに保存
  useEffect(() => {
    if (referenceLogs.length > 0) {
      localStorage.setItem(`referenceLogs_${proposal.id}`, JSON.stringify(referenceLogs));
    }
  }, [referenceLogs, proposal.id]);

  // デバッグログ
  console.log('ProposalCard - referenceLogs:', referenceLogs);
  console.log('ProposalCard - referenceLogs.length:', referenceLogs.length);

  // 評価権限の確認（自分の解決案は評価不可）
  const canEvaluate = user?.user_type === 'proposer' && user.username !== proposal.proposer_name;
  
  // 評価データを取得
  useEffect(() => {
    if (canEvaluate) {
      const fetchEvaluation = async () => {
        try {
          const evaluation = await getProposalEvaluation(proposal.id);
          setUserEvaluation(evaluation);
        } catch (error) {
          console.error('評価データ取得エラー:', error);
        }
      };
      fetchEvaluation();
    }
  }, [proposal.id, canEvaluate]);
  
  // コメント権限の確認
  const canComment = user?.user_type === 'proposer' && user.username !== proposal.proposer_name;
  
  // 返信権限の確認（提案者のみ）
  const canReply = user?.username === proposal.proposer_name;
  
  // 参考権限の確認（自分の解決案の場合のみ）
  const canReference = user?.username === proposal.proposer_name;

  // 評価ハンドラー
  const handleEvaluate = async (proposalId: number, evaluation: 'yes' | 'maybe' | 'no') => {
    if (!canEvaluate) return;
    
    setIsEvaluating(true);
    try {
      const result = await createProposalEvaluation(proposalId, { evaluation });
      setUserEvaluation(result);
    } catch (error) {
      console.error('評価エラー:', error);
      alert('評価の投稿に失敗しました。');
    } finally {
      setIsEvaluating(false);
    }
  };

  // コメント追加ハンドラー
  const handleAddComment = async (comment: any) => {
    if (!canComment) return;
    
    setIsAddingComment(true);
    try {
      const result = await createProposalComment(proposal.id, comment);
      setComments(prev => [...prev, result]);
      
      // total_comment_countを更新
      if (proposal.total_comment_count !== undefined) {
        proposal.total_comment_count += 1;
      }
      
      alert('コメントを投稿しました。');
    } catch (error: any) {
      console.error('コメントエラー:', error);
      alert('コメントの投稿に失敗しました。');
    } finally {
      setIsAddingComment(false);
    }
  };

  // 返信ハンドラー
  const handleReply = async (commentId: number, reply: any) => {
    if (!canReply) return;
    
    setIsReplying(true);
    try {
      const result = await createProposalCommentReply(commentId, reply);
      // コメントリストを更新
      setComments(prev => prev.map(comment => 
        comment.id === commentId 
          ? { ...comment, replies: [...(comment.replies || []), result] }
          : comment
      ));
      
      // total_comment_countを更新（返信もコメントとしてカウント）
      if (proposal.total_comment_count !== undefined) {
        proposal.total_comment_count += 1;
      }
    } catch (error) {
      console.error('返信エラー:', error);
      alert('返信の投稿に失敗しました。');
    } finally {
      setIsReplying(false);
    }
  };

  // 参考ハンドラー（解決案編集機能）
  const handleReference = (commentId: number) => {
    if (!canReference) return;
    
    // コメントを参考にして解決案を編集する機能
    alert(`コメントID ${commentId} を参考に解決案を編集します。\nこの機能では、コメントの内容を参考にして解決案の結論や理由を改善できます。`);
    
    // TODO: 解決案編集ページに遷移する実装
    // router.push(`/proposals/${proposal.id}/edit?reference=${commentId}`);
  };

  // 解決案編集ハンドラー
  const handleEdit = async (proposalId: number, data: { conclusion: string; reasoning: string }) => {
    console.log('handleEdit called:', { proposalId, data, canReference, editingCommentId });
    if (!canReference) return;
    
    setIsEditing(true);
    try {
      // 解決案を更新
      const updatedProposal = {
        ...proposalState,
        conclusion: data.conclusion,
        reasoning: data.reasoning
      };
      setProposalState(updatedProposal);
      
      // 編集された解決案をlocalStorageに保存
      localStorage.setItem(`editedProposal_${proposal.id}`, JSON.stringify({
        conclusion: data.conclusion,
        reasoning: data.reasoning
      }));
      
      // 参考ログを追加
      const referenceLog: ReferenceLog = {
        id: `ref_${Date.now()}`,
        commentId: editingCommentId || 0,
        commentConclusion: comments.find(c => c.id === editingCommentId)?.conclusion || '',
        editedAt: new Date().toISOString()
      };
      console.log('Adding referenceLog:', referenceLog);
      setReferenceLogs(prev => {
        const newLogs = [...prev, referenceLog];
        console.log('New referenceLogs:', newLogs);
        return newLogs;
      });
      
      alert(`解決案を編集しました。`);
    } catch (error) {
      console.error('解決案編集エラー:', error);
      alert('解決案の編集に失敗しました。');
    } finally {
      setIsEditing(false);
      setEditingCommentId(null);
    }
  };

  // コメントセクション表示ハンドラー
  const handleShowComments = async () => {
    const willShow = !showCommentsSection;
    setShowCommentsSection(willShow);
    
    // コメントセクションを開く場合、コメント一覧を取得
    if (willShow) {
      try {
        const response = await getProposalComments(proposal.id);
        setComments(response.results);
        
        // 未読コメント数をリセット
        setUnreadCount(0);
      } catch (error) {
        console.error('コメント取得エラー:', error);
      }
    }
    
    if (onComments) {
      // 未読数を更新したproposalを渡す
      const updatedProposal = { ...proposal, unread_comment_count: 0 };
      onComments(updatedProposal);
    }
  };

  // 日付フォーマット関数
  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('ja-JP', {
      year: 'numeric',
      month: 'numeric',
      day: 'numeric'
    });
  };

  // ステータス表示
  const getStatusDisplay = (status: string) => {
    switch (status) {
      case 'submitted':
        return { label: '投稿済み', color: 'bg-blue-100 text-blue-800' };
      case 'under_review':
        return { label: '審査中', color: 'bg-yellow-100 text-yellow-800' };
      case 'adopted':
        return { label: '採用', color: 'bg-green-100 text-green-800' };
      case 'rejected':
        return { label: '却下', color: 'bg-red-100 text-red-800' };
      default:
        return { label: '下書き', color: 'bg-gray-100 text-gray-800' };
    }
  };

  const statusDisplay = getStatusDisplay(proposal.status);

  // 評価済み解決案の視覚的フィードバック
  const isEvaluated = userEvaluation !== null;
  const cardClassName = isEvaluated 
    ? "bg-gray-100 border border-gray-300 rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200 p-6 opacity-75"
    : "bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200 p-6";

  return (
    <div className={cardClassName}>
      {/* ヘッダー */}
      <div className="mb-4">
        <div className="flex justify-between items-start mb-3">
          <div className="flex items-center gap-2">
            {showStatus && (
              <span className={`px-3 py-1 text-sm rounded-full ${statusDisplay.color}`}>
                {statusDisplay.label}
              </span>
            )}
            {isEvaluated && (
              <span className="px-3 py-1 text-sm rounded-full bg-blue-600 text-white">
                評価済み
              </span>
            )}
          </div>
          <div className="flex items-center gap-4 text-sm text-gray-600">
            <span>提案者: {proposal.proposer_name}</span>
            <span>投稿日: {formatDate(proposal.created_at)}</span>
          </div>
        </div>
      </div>

      {/* 結論 */}
      <div className="mb-4">
        <h4 className="text-base font-medium text-gray-700 mb-2">【結論】</h4>
        <div className="bg-pink-50 rounded-lg p-3">
          <p className="text-gray-700 leading-relaxed line-clamp-3">
            {proposalState.conclusion || '結論が設定されていません'}
          </p>
        </div>
      </div>

      {/* 理由 */}
      <div className="mb-4">
        <h4 className="text-base font-medium text-gray-700 mb-2">【理由】</h4>
        <div className="bg-green-50 rounded-lg p-3">
          <p className="text-gray-700 leading-relaxed line-clamp-3">
            {proposalState.reasoning || '理由が設定されていません'}
          </p>
        </div>
      </div>

      {/* 課題情報 */}
      {showChallengeInfo && (
        <div className="mb-4">
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-sm text-gray-600 mb-1">対象課題</p>
            {(() => {
              const targetChallengeId = challengeId || proposal.challenge_id;
              console.log('ProposalCard - proposal.challenge_id:', proposal.challenge_id, 'challengeId:', challengeId, 'targetChallengeId:', targetChallengeId);
              return targetChallengeId && !isNaN(targetChallengeId) ? (
                <Link 
                  href={`/challenges/${targetChallengeId}`}
                  className="font-medium text-blue-600 hover:text-blue-800 hover:underline cursor-pointer"
                >
                  {proposal.challenge_title}
                </Link>
              ) : (
                <p className="font-medium text-gray-900">{proposal.challenge_title}</p>
              );
            })()}
          </div>
        </div>
      )}

      {/* 評価情報 */}
      {proposal.rating_count > 0 && (
        <div className="mb-4">
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-1">
              <span className="text-yellow-500">★</span>
              <span className="font-medium">{proposal.rating?.toFixed(1) || 'N/A'}</span>
              <span className="text-gray-500">({proposal.rating_count}件)</span>
            </div>
          </div>
        </div>
      )}

      {/* アクションボタン */}
      {showActions && (
        <div className="flex gap-4 pt-4 border-t border-gray-200">
          {onView && (
            <button
              onClick={() => onView(proposal)}
              className="flex-1 bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors duration-200 font-medium cursor-pointer"
            >
              詳細を見る
            </button>
          )}
          {showEditDelete && onEdit && (
            <button
              onClick={() => onEdit(proposal)}
              className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors duration-200 font-medium cursor-pointer"
            >
              編集
            </button>
          )}
          {showEditDelete && onDelete && (
            <button
              onClick={() => onDelete(proposal)}
              className="px-6 py-3 border border-red-300 text-red-700 rounded-lg hover:bg-red-50 transition-colors duration-200 font-medium cursor-pointer"
            >
              削除
            </button>
          )}
        </div>
      )}

      {/* 参考にしたコメントセクション */}
      {referenceLogs.length > 0 && (
        <div className="mt-6 pt-6 border-t border-gray-200">
          <h4 className="text-sm font-medium text-gray-700 mb-3">参考にしたコメント</h4>
          <div className="space-y-3">
            {referenceLogs.map((log) => (
              <div key={log.id} className="space-y-2">
                <h5 className="text-sm font-medium text-gray-700">【結論】</h5>
                <div className="bg-pink-50 rounded-lg p-3">
                  <p className="text-gray-700 leading-relaxed">
                    {log.commentConclusion}
                  </p>
                </div>
                <p className="text-xs text-gray-500">
                  編集日時: {new Date(log.editedAt).toLocaleString('ja-JP')}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 評価・コメントセクション */}
      {showComments && (
        <div className="mt-6 pt-6 border-t border-gray-200">
          <div className="space-y-4">
            {canEvaluate && (
              <ProposalEvaluationComponent
                proposalId={proposal.id}
                userEvaluation={userEvaluation || undefined}
                onEvaluate={handleEvaluate}
                isEvaluating={isEvaluating}
              />
            )}
            <button
              onClick={handleShowComments}
              className="w-full bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors duration-200 font-medium cursor-pointer relative"
            >
              {showCommentsSection ? 'コメントを閉じる' : `コメント（${proposal.total_comment_count || 0}）`}
              {!showCommentsSection && unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                  {unreadCount}
                </span>
              )}
            </button>
          </div>
        </div>
      )}

      {/* コメントセクション */}
      {showCommentsSection && (
        <div className="mt-6 pt-6 border-t border-gray-200">
          <ProposalCommentList
            proposalId={proposal.id}
            proposal={proposal}
            proposalState={proposalState}
            comments={comments}
            onAddComment={handleAddComment}
            onReply={handleReply}
            onEdit={handleEdit}
            onReference={handleReference}
            isAddingComment={isAddingComment}
            isReplying={isReplying}
            isEditing={isEditing}
            editingCommentId={editingCommentId}
            setEditingCommentId={setEditingCommentId}
            canComment={canComment}
            canReply={canReply}
            canReference={canReference}
          />
        </div>
      )}
    </div>
  );
};

export default ProposalCard;
