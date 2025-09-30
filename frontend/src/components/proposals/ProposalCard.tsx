/**
 * 提案カードコンポーネント
 * 提案一覧での表示用
 */
import React from 'react';
import Link from 'next/link';
import type { ProposalListItem, ProposalCardProps } from '@/types/proposal';

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

  return (
    <div className="bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200 p-6">
      {/* ヘッダー */}
      <div className="mb-4">
        <div className="flex justify-between items-start mb-3">
          {showStatus && (
            <span className={`px-3 py-1 text-sm rounded-full ${statusDisplay.color}`}>
              {statusDisplay.label}
            </span>
          )}
          <div className="flex items-center gap-4 text-sm text-gray-600">
            <span>提案者: {proposal.proposer_name}</span>
            <span>投稿日: {formatDate(proposal.created_at)}</span>
          </div>
        </div>
      </div>

      {/* 結論 */}
      <div className="mb-4">
        <h4 className="text-sm font-medium text-gray-700 mb-2">結論</h4>
        <div className="bg-pink-50 rounded-lg p-3">
          <p className="text-gray-700 leading-relaxed line-clamp-3">
            {proposal.conclusion || '結論が設定されていません'}
          </p>
        </div>
      </div>

      {/* 理由 */}
      <div className="mb-4">
        <h4 className="text-sm font-medium text-gray-700 mb-2">理由</h4>
        <div className="bg-green-50 rounded-lg p-3">
          <p className="text-gray-700 leading-relaxed line-clamp-3">
            {proposal.reasoning || '理由が設定されていません'}
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
          {showComments && onComments && (
            <button
              onClick={() => onComments(proposal)}
              className="w-full bg-blue-600 text-white px-8 py-3 rounded-lg hover:bg-blue-700 transition-colors duration-200 font-medium cursor-pointer"
            >
              コメント
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default ProposalCard;
