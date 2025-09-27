/**
 * 提案カードコンポーネント
 * 提案一覧表示用のカード形式UI
 */
import React from 'react';
import type { ProposalListItem, ProposalCardProps } from '../../types/proposal';

const ProposalCard: React.FC<ProposalCardProps> = ({
  proposal,
  showActions = false,
  onView,
  onEdit,
  onDelete,
  onAdopt
}) => {
  // 提案者の表示名
  const proposerName = proposal.proposer_name || '不明';

  // 提案の作成日時
  const formatCreatedAt = (createdAt: string) => {
    const date = new Date(createdAt);
    return date.toLocaleDateString('ja-JP', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // 結論の表示（長い場合は省略）
  const truncateConclusion = (conclusion: string, maxLength: number = 100) => {
    if (conclusion.length <= maxLength) {
      return conclusion;
    }
    return conclusion.substring(0, maxLength) + '...';
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200 p-6">
      {/* ヘッダー部分 */}
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            {proposal.challenge_title}
          </h3>
          <p className="text-sm text-gray-600">
            提案者: {proposerName}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {proposal.is_adopted && (
            <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">
              採用済み
            </span>
          )}
          <span className="text-sm text-gray-500">
            {formatCreatedAt(proposal.created_at)}
          </span>
        </div>
      </div>

      {/* 提案内容 */}
      <div className="mb-4">
        <h4 className="text-sm font-medium text-gray-700 mb-2">結論</h4>
        <p className="text-gray-900 text-sm leading-relaxed">
          {truncateConclusion(proposal.conclusion)}
        </p>
      </div>

      {/* 評価情報 */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-4 text-sm text-gray-600">
          <span>評価数: {proposal.evaluation_count}件</span>
        </div>
      </div>

      {/* アクションボタン */}
      {showActions && (
        <div className="flex gap-2 pt-4 border-t border-gray-100">
          {onView && (
            <button
              onClick={() => onView(proposal)}
              className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors duration-200 text-sm font-medium"
            >
              詳細を見る
            </button>
          )}
          {onEdit && (
            <button
              onClick={() => onEdit(proposal)}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors duration-200 text-sm font-medium"
            >
              編集
            </button>
          )}
          {onAdopt && (
            <button
              onClick={() => onAdopt(proposal)}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors duration-200 text-sm font-medium"
            >
              採用
            </button>
          )}
          {onDelete && (
            <button
              onClick={() => onDelete(proposal)}
              className="px-4 py-2 border border-red-300 text-red-700 rounded-lg hover:bg-red-50 transition-colors duration-200 text-sm font-medium"
            >
              削除
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default ProposalCard;
