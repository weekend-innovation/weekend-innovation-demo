/**
 * 課題カードコンポーネント
 * 課題一覧表示用のカード形式UI
 */
import React from 'react';
import type { ChallengeCardProps } from '../../types/challenge';
import { isProposerExpiredOrFailed, isAllPhasesCompleted, isContributorExpired, canProposerViewResults } from '../../lib/challengeSortUtils';
import { DemoRewardAmountPlaceholder } from '../common/DemoRewardDisclaimer';

const ChallengeCard: React.FC<ChallengeCardProps> = ({
  challenge,
  showActions = false,
  userType = 'contributor',
  isProposed = false,
  onView,
  onEdit,
  onDelete
}) => {
  const expiredOrFailed = userType === 'proposer' && isProposerExpiredOrFailed(challenge);
  const allPhasesDone = userType === 'proposer' && isAllPhasesCompleted(challenge);
  const canViewResults = userType === 'proposer' && canProposerViewResults(challenge);
  const proposerChallengeCompleted =
    userType === 'proposer' && challenge.status === 'completed';
  const proposerPendingAdoptionAfterParticipation =
    userType === 'proposer' &&
    challenge.status === 'closed' &&
    canViewResults;
  const contributorAdoptionFinalized =
    userType === 'contributor' && challenge.status === 'completed';
  const contributorPastDeadlineUnfinalized =
    userType === 'contributor' &&
    !contributorAdoptionFinalized &&
    isContributorExpired(challenge);
  /** 期限切れ（提案者・結果閲覧不可）は赤みの薄さで示す */
  const passiveExpiredCardStyle =
    'bg-red-50 border border-red-300 opacity-60';
  const isProposerExpiredLockedOut =
    userType === 'proposer' && expiredOrFailed && !canViewResults;
  /** 採用完了など「完了」はグレー系の薄さ（赤は使わない） */
  const grayCompletedCardStyle =
    'bg-gray-100 border border-gray-400 opacity-95 text-gray-600';
  const mutedCompletedChallenge =
    contributorAdoptionFinalized || proposerChallengeCompleted;

  // 提案者用: 現在のフェーズの期限ラベルと値を取得（ソート順が分かるように）
  const getCurrentPhaseDeadlineInfo = (): { label: string; value: string } | null => {
    if (userType !== 'proposer' || expiredOrFailed) return null;
    const p = challenge.current_phase;
    if (p === 'proposal' && challenge.proposal_deadline)
      return { label: '提案期限', value: challenge.proposal_deadline };
    if (p === 'edit' && challenge.edit_deadline)
      return { label: '編集期限', value: challenge.edit_deadline };
    if (p === 'evaluation' && challenge.evaluation_deadline)
      return { label: '評価期限', value: challenge.evaluation_deadline };
    return null;
  };

  // 期限の表示形式
  const formatDeadline = (deadline: string) => {
    const date = new Date(deadline);
    // UTCの値をそのまま使用（日本時間への変換を避ける）
    const year = date.getUTCFullYear();
    const month = date.getUTCMonth() + 1;
    const day = date.getUTCDate();
    const hours = String(date.getUTCHours()).padStart(2, '0');
    const minutes = String(date.getUTCMinutes()).padStart(2, '0');
    return `${year}年${month}月${day}日 ${hours}:${minutes}`;
  };

  const cardStyle = mutedCompletedChallenge
    ? grayCompletedCardStyle
    : userType === 'proposer'
      ? proposerPendingAdoptionAfterParticipation
        ? 'bg-amber-50 border border-amber-200'
        : isProposerExpiredLockedOut
          ? passiveExpiredCardStyle
          : allPhasesDone
            ? 'bg-teal-50 border border-teal-300'
            : 'bg-white border border-gray-200'
      : contributorPastDeadlineUnfinalized
        ? 'bg-amber-50 border border-amber-200'
        : 'bg-white border border-gray-200';

  return (
    <div className={`rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200 p-6 min-w-0 ${cardStyle}`}>
      {/* タイトル */}
      <div className="mb-4">
        <div className="flex justify-end mb-2 gap-2 flex-wrap">
          {userType === 'proposer' && expiredOrFailed && !canViewResults && (
            <span className="px-3 py-1 text-sm rounded-lg font-medium text-red-600 bg-red-100">
              期限切れ
            </span>
          )}
          {userType === 'proposer' && proposerChallengeCompleted && (
            <span className="px-3 py-1 text-sm rounded-lg font-medium text-gray-600 bg-gray-200 border border-gray-400">
              完了
            </span>
          )}
          {userType === 'proposer' && proposerPendingAdoptionAfterParticipation && (
            <span className="px-3 py-1 text-sm rounded-lg font-medium text-amber-800 bg-amber-100 border border-amber-300">
              期間満了（採用未確定）
            </span>
          )}
          {userType === 'proposer' && allPhasesDone && (
            <span className="px-3 py-1 text-sm rounded-lg font-medium text-teal-700 bg-teal-100">
              全フェーズ達成
            </span>
          )}
          {userType === 'proposer' && !expiredOrFailed && !allPhasesDone && challenge.phase_display && (
            <span className={`px-3 py-1 text-sm rounded-lg font-medium ${
              challenge.current_phase === 'proposal' ? 'text-green-600 bg-green-100' :
              challenge.current_phase === 'edit' ? 'text-yellow-600 bg-yellow-100' :
              challenge.current_phase === 'evaluation' ? 'text-orange-600 bg-orange-100' :
              'text-gray-600 bg-gray-100'
            }`}>
              {challenge.phase_display}
            </span>
          )}
          {userType === 'contributor' && contributorAdoptionFinalized && (
            <span className="px-3 py-1 text-sm rounded-lg font-medium text-gray-600 bg-gray-200 border border-gray-400">
              完了
            </span>
          )}
          {userType === 'contributor' && contributorPastDeadlineUnfinalized && (
            <span className="px-3 py-1 text-sm rounded-lg font-medium text-amber-800 bg-amber-100 border border-amber-300">
              期間満了（採用未確定）
            </span>
          )}
          {userType === 'contributor' &&
            !contributorAdoptionFinalized &&
            !contributorPastDeadlineUnfinalized &&
            challenge.phase_display && (
              <span
                className={`px-3 py-1 text-sm rounded-lg font-medium ${
                  challenge.current_phase === 'proposal'
                    ? 'text-green-600 bg-green-100'
                    : challenge.current_phase === 'edit'
                      ? 'text-yellow-600 bg-yellow-100'
                      : challenge.current_phase === 'evaluation'
                        ? 'text-orange-600 bg-orange-100'
                        : 'text-gray-600 bg-gray-100'
                }`}
              >
                {challenge.phase_display}
              </span>
            )}
          {isProposed && !expiredOrFailed && !allPhasesDone && (
            <span className="px-3 py-1 text-sm rounded-lg bg-blue-600 text-white font-medium">
              提案済み
            </span>
          )}
          {challenge.has_completed_all_evaluations && !allPhasesDone && !expiredOrFailed && (
            <span className="px-3 py-1 text-sm rounded-lg bg-purple-600 text-white font-medium">
              ✓ 全評価完了
            </span>
          )}
        </div>
        <div className="flex items-start justify-between gap-4 mb-3 min-w-0">
          <h3
            className={`text-xl flex-1 min-w-0 pr-2 break-words ${
              mutedCompletedChallenge ? 'font-semibold text-gray-500' : 'font-bold text-gray-900'
            }`}
          >
            {challenge.title}
          </h3>
          <div className="text-right flex-shrink-0">
            <div
              className={`flex items-center gap-4 text-sm flex-wrap justify-end ${
                mutedCompletedChallenge ? 'text-gray-500' : 'text-gray-600'
              }`}
            >
              <span>投稿者: {challenge.contributor_name}</span>
              <span>投稿日: {new Date(challenge.created_at).toLocaleDateString('ja-JP')}</span>
            </div>
          </div>
        </div>
      </div>

      {/* 説明文 */}
      <div className="mb-4">
        <p
          className={`leading-relaxed ${
            mutedCompletedChallenge ? 'text-gray-500' : 'text-gray-700'
          }`}
        >
          {challenge.description}
        </p>
      </div>

      {/* 報酬情報（デモ: 金額は伏せてプレースホルダのみ） */}
      <div className="grid grid-cols-2 gap-4 mb-2">
        <div
          className={`rounded-lg p-4 text-center ${
            mutedCompletedChallenge ? 'bg-blue-50/70 opacity-90' : 'bg-blue-50'
          }`}
        >
          <p className="text-sm text-blue-600 font-medium mb-2">提案報酬</p>
          <p className="text-2xl font-bold text-blue-900">
            <DemoRewardAmountPlaceholder className="text-2xl font-bold text-blue-900" />
          </p>
        </div>
        <div
          className={`rounded-lg p-4 text-center ${
            mutedCompletedChallenge ? 'bg-green-50/70 opacity-90' : 'bg-green-50'
          }`}
        >
          <p className="text-sm text-green-600 font-medium mb-2">採用報酬</p>
          <p className="text-2xl font-bold text-green-900">
            <DemoRewardAmountPlaceholder className="text-2xl font-bold text-green-900" />
          </p>
        </div>
      </div>
      {/* 詳細情報 */}
      <div
        className={`rounded-lg p-3 mb-4 min-w-0 ${
          mutedCompletedChallenge ? 'bg-gray-100/80' : 'bg-gray-50'
        }`}
      >
        <div
          className={`flex justify-between items-center gap-4 text-sm flex-wrap ${
            mutedCompletedChallenge ? 'text-gray-500' : 'text-gray-600'
          }`}
        >
          <span className="font-medium">選出人数: {challenge.required_participants}人</span>
          <span className="font-medium">
            {(() => {
              const info = getCurrentPhaseDeadlineInfo();
              if (info) return `${info.label}: ${formatDeadline(info.value)}`;
              return `期限: ${formatDeadline(challenge.deadline)}`;
            })()}
          </span>
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