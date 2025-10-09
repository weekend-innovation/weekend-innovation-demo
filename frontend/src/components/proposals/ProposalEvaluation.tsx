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
  console.log('ProposalEvaluation レンダリング:', { 
    proposalId, 
    userEvaluation: userEvaluation ? {
      evaluation: userEvaluation.evaluation,
      score: userEvaluation.score,
      id: userEvaluation.id
    } : null, 
    isEvaluating 
  });
  const [selectedEvaluation, setSelectedEvaluation] = useState<'yes' | 'maybe' | 'no' | null>(
    userEvaluation?.evaluation || null
  );

  const handleEvaluation = (evaluation: 'yes' | 'maybe' | 'no') => {
    console.log('評価ボタンクリック:', { proposalId, evaluation, userEvaluation });
    
    // 既に評価済みの場合は変更不可
    if (userEvaluation) {
      console.log('既に評価済みのため処理をスキップ');
      return;
    }
    
    console.log('評価処理開始');
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

  const buttonDisabled = isEvaluating || !!userEvaluation;
  console.log('評価ボタン状態:', { 
    isEvaluating, 
    userEvaluation: !!userEvaluation, 
    buttonDisabled,
    selectedEvaluation 
  });

  // 評価済みの場合の表示
  console.log('評価表示判定:', { 
    hasUserEvaluation: !!userEvaluation,
    userEvaluationData: userEvaluation,
    willShowEvaluated: !!userEvaluation
  });
  
  if (userEvaluation) {
    return (
      <div className="bg-blue-50 rounded-lg p-4 mb-4 border border-blue-200">
        <h4 className="text-sm font-medium text-blue-700 mb-3 text-center">【評価済み】</h4>
        <div className="flex gap-2 justify-center">
          {(['no', 'maybe', 'yes'] as const).map((evaluation) => (
            <button
              key={evaluation}
              disabled={true}
              className={`
                px-4 py-2 rounded-lg font-medium text-sm transition-colors duration-200
                ${userEvaluation.evaluation === evaluation 
                  ? getEvaluationColor(evaluation)
                  : 'bg-gray-200 text-gray-400'
                }
                opacity-50 cursor-not-allowed
              `}
            >
              {getEvaluationLabel(evaluation)}
            </button>
          ))}
        </div>
      </div>
    );
  }

  // 評価未実施の場合
  return (
    <div className="bg-gray-50 rounded-lg p-4 mb-4">
      <h4 className="text-sm font-medium text-gray-700 mb-3 text-center">【評価】この結論は思い付いていましたか？</h4>
      <div className="flex gap-2 justify-center">
        {(['no', 'maybe', 'yes'] as const).map((evaluation) => (
          <button
            key={evaluation}
            onClick={() => handleEvaluation(evaluation)}
            disabled={buttonDisabled}
            className={`
              px-4 py-2 rounded-lg font-medium text-sm transition-colors duration-200
              ${selectedEvaluation === evaluation 
                ? getEvaluationColor(evaluation)
                : 'bg-gray-200 hover:bg-gray-300 text-gray-700'
              }
              ${buttonDisabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
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