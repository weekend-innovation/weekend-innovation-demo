/**
 * 課題カードコンポーネント
 * 課題一覧表示用のカード形式UI
 */
import React from 'react';
import type { ChallengeListItem, ChallengeCardProps } from '../../types/challenge';

const ChallengeCard: React.FC<ChallengeCardProps> = ({
  challenge,
  showActions = false,
  onView,
  onEdit,
  onDelete
}) => {
  // ステータスに応じた表示色とラベル
  const getStatusDisplay = (status: string) => {
    switch (status) {
      case 'open':
        return { label: '募集中', color: 'text-green-600 bg-green-100' };
      case 'closed':
        return { label: '締切', color: 'text-red-600 bg-red-100' };
      case 'completed':
        return { label: '完了', color: 'text-blue-600 bg-blue-100' };
      default:
        return { label: status, color: 'text-gray-600 bg-gray-100' };
    }
  };

  // 期限の表示形式
  const formatDeadline = (deadline: string) => {
    const date = new Date(deadline);
    return date.toLocaleDateString('ja-JP', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // 報酬の表示形式
  const formatReward = (amount: number) => {
    return `¥${amount.toLocaleString()}`;
  };

  const statusDisplay = getStatusDisplay(challenge.status);

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200 p-6">
      {/* ヘッダー部分 */}
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2">
            {challenge.title}
          </h3>
          <p className="text-sm text-gray-600">
            投稿者: {challenge.contributor_name}
          </p>
        </div>
        <span className={`px-2 py-1 text-xs font-medium rounded-full ${statusDisplay.color}`}>
          {statusDisplay.label}
        </span>
      </div>

      {/* 報酬情報 */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="bg-gray-50 rounded-lg p-3">
          <p className="text-xs text-gray-500 mb-1">提案報酬</p>
          <p className="text-lg font-semibold text-gray-900">
            {formatReward(challenge.reward_amount)}
          </p>
        </div>
        <div className="bg-gray-50 rounded-lg p-3">
          <p className="text-xs text-gray-500 mb-1">採用報酬</p>
          <p className="text-lg font-semibold text-gray-900">
            {formatReward(challenge.adoption_reward)}
          </p>
        </div>
      </div>

      {/* 選出人数と期限 */}
      <div className="flex justify-between items-center text-sm text-gray-600 mb-4">
        <span>選出人数: {challenge.required_participants}人</span>
        <span>期限: {formatDeadline(challenge.deadline)}</span>
      </div>

      {/* アクションボタン */}
      {showActions && (
        <div className="flex gap-2 pt-4 border-t border-gray-100">
          {onView && (
            <button
              onClick={() => onView(challenge)}
              className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors duration-200 text-sm font-medium"
            >
              詳細を見る
            </button>
          )}
          {onEdit && (
            <button
              onClick={() => onEdit(challenge)}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors duration-200 text-sm font-medium"
            >
              編集
            </button>
          )}
          {onDelete && (
            <button
              onClick={() => onDelete(challenge)}
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

export default ChallengeCard;
