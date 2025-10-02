/**
 * 提案評価コンポーネント
 * 同じく選出された提案者のみが評価可能
 */
import React, { useState } from 'react';
import type { ProposalEvaluationProps } from '../../types/proposal';

const ProposalEvaluation: React.FC<ProposalEvaluationProps> = ({
  proposalId,
  userEvaluation,
  onEvaluate,
  isEvaluating = false
}) => {
  const [selectedEvaluation, setSelectedEvaluation] = useState<'yes' | 'maybe' | 'no' | null>(
    userEvaluation?.evaluation || null
  );

  const handleEvaluation = (evaluation: 'yes' | 'maybe' | 'no') => {
    // 既に評価済みの場合は変更不可
    if (userEvaluation) {
      return;
    }
    setSelectedEvaluation(evaluation);
    onEvaluate(proposalId, evaluation);
  };

  const getEvaluationColor = (evaluation: 'yes' | 'maybe' | 'no') => {
    switch (evaluation) {
      case 'no':
        return 'bg-red-500 hover:bg-red-600 text-white';
      case 'maybe':
        return 'bg-yellow-500 hover:bg-yellow-600 text-white';
      case 'yes':
        return 'bg-green-500 hover:bg-green-600 text-white';
      default:
        return 'bg-gray-200 hover:bg-gray-300 text-gray-700';
    }
  };

  const getEvaluationLabel = (evaluation: 'yes' | 'maybe' | 'no') => {
    switch (evaluation) {
      case 'no':
        return 'No';
      case 'maybe':
        return 'Maybe';
      case 'yes':
        return 'Yes';
    }
  };

  return (
    <div className="bg-gray-50 rounded-lg p-4 mb-4">
      <h4 className="text-sm font-medium text-gray-700 mb-3 text-center">【評価】この結論は思い付いていましたか？</h4>
      <div className="flex gap-2 justify-center">
        {(['no', 'maybe', 'yes'] as const).map((evaluation) => (
          <button
            key={evaluation}
            onClick={() => handleEvaluation(evaluation)}
            disabled={isEvaluating || userEvaluation !== null}
            className={`
              px-4 py-2 rounded-lg font-medium text-sm transition-colors duration-200
              ${selectedEvaluation === evaluation 
                ? getEvaluationColor(evaluation)
                : 'bg-gray-200 hover:bg-gray-300 text-gray-700'
              }
              ${isEvaluating || userEvaluation ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
          >
            {getEvaluationLabel(evaluation)}
          </button>
        ))}
      </div>
    </div>
  );
};

export default ProposalEvaluation;