/**
 * 課題カードコンポーネント
 * 課題一覧表示用のカード形式UI
 */
import React from 'react';
import type { ChallengeListItem, ChallengeCardProps } from '../../types/challenge';

const ChallengeCard: React.FC<ChallengeCardProps> = ({
  challenge,
  showActions = false,
  userType = 'contributor',
  isProposed = false,
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
        return { label: '期限切れ', color: 'text-red-600 bg-red-100' };
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
      day: 'numeric'
    });
  };

  // 報酬の表示形式
  const formatReward = (amount: number) => {
    // 0の場合は空文字を返す
    if (amount === 0) {
      return '';
    }
    // 1万円未満の場合は円単位で表示
    if (amount < 10000) {
      return `${amount}円`;
    }
    // 1万円以上の場合は万円単位で表示
    const amountInMan = amount / 10000;
    // 整数の場合は小数点を表示しない
    if (amountInMan % 1 === 0) {
      return `${Math.floor(amountInMan)}万円`;
    }
    // 小数点がある場合は1桁まで表示
    return `${amountInMan.toFixed(1)}万円`;
  };

  const statusDisplay = getStatusDisplay(challenge.status);

  return (
    <div className={`rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200 p-6 ${
      challenge.status === 'closed'
        ? 'bg-red-50 border border-red-300 opacity-60' 
        : challenge.status === 'completed'
        ? 'bg-blue-50 border border-blue-300 opacity-75'
        : isProposed
        ? 'bg-gray-200 border border-gray-500 opacity-50'
        : 'bg-white border border-gray-200'
    }`}>
      {/* タイトル */}
      <div className="mb-4">
        <div className="flex justify-end mb-2 gap-2">
          {isProposed && (
            <span className="px-3 py-1 text-sm rounded-full bg-blue-600 text-white font-medium">
              提案済み
            </span>
          )}
          <span className={`px-3 py-1 text-sm rounded-full font-medium ${statusDisplay.color}`}>
            {statusDisplay.label}
          </span>
        </div>
        <div className="flex items-start justify-between mb-3">
          <h3 className="text-xl font-bold text-gray-900 flex-1 pr-4">
            {challenge.title}
          </h3>
          <div className="text-right">
            <div className="flex items-center gap-4 text-sm text-gray-600">
              <span>投稿者: {challenge.contributor_name}</span>
              <span>投稿日: {new Date(challenge.created_at).toLocaleDateString('ja-JP')}</span>
            </div>
          </div>
        </div>
      </div>

      {/* 説明文 */}
      <div className="mb-4">
        <p className="text-gray-700 leading-relaxed">
          {challenge.description}
        </p>
      </div>

      {/* 報酬情報 */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="bg-blue-50 rounded-lg p-4 text-center">
          <p className="text-sm text-blue-600 font-medium mb-2">提案報酬</p>
          <p className="text-2xl font-bold text-blue-900">
            {formatReward(challenge.reward_amount)}
          </p>
        </div>
        <div className="bg-green-50 rounded-lg p-4 text-center">
          <p className="text-sm text-green-600 font-medium mb-2">採用報酬</p>
          <p className="text-2xl font-bold text-green-900">
            {formatReward(challenge.adoption_reward)}
          </p>
        </div>
      </div>

      {/* 詳細情報 */}
      <div className="bg-gray-50 rounded-lg p-3 mb-4">
        <div className="flex justify-between items-center text-sm text-gray-600">
          <span className="font-medium">選出人数: {challenge.required_participants}人</span>
          <span className="font-medium">期限: {formatDeadline(challenge.deadline)}</span>
        </div>
      </div>

      {/* アクションボタン */}
      {showActions && (
        <div className="flex gap-4 pt-4 border-t border-gray-200">
          {userType === 'contributor' ? (
            <>
              {onView && (
                <button
                  onClick={() => onView(challenge)}
                  className="flex-1 bg-gray-100 text-gray-700 px-6 py-3 rounded-lg hover:bg-gray-300 hover:shadow-md transition-all duration-200 font-medium border border-gray-300 cursor-pointer"
                >
                  詳細を見る
                </button>
              )}
              {onEdit && (
                <button
                  onClick={() => onEdit(challenge)}
                  className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors duration-200 font-medium cursor-pointer"
                >
                  編集
                </button>
              )}
              {onDelete && (
                <button
                  onClick={() => onDelete(challenge)}
                  className="px-6 py-3 border border-red-300 text-red-700 rounded-lg hover:bg-red-50 transition-colors duration-200 font-medium cursor-pointer"
                >
                  削除
                </button>
              )}
            </>
          ) : (
            /* 提案者の場合 */
            onView && (
              <button
                onClick={() => onView(challenge)}
                className="flex-1 bg-gray-100 text-gray-700 px-6 py-3 rounded-lg hover:bg-gray-300 hover:shadow-md transition-all duration-200 font-medium border border-gray-300 cursor-pointer"
              >
                詳細を見る
              </button>
            )
          )}
        </div>
      )}
    </div>
  );
};

export default ChallengeCard;