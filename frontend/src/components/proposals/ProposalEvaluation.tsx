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
  const [selectedInsightLevel, setSelectedInsightLevel] = useState<'1' | '2' | '3' | '4' | '5' | null>(
    userEvaluation?.insight_level || null
  );

  const handleEvaluation = (evaluation: 'yes' | 'maybe' | 'no') => {
    // 既に評価済みの場合は変更不可
    if (userEvaluation) {
      return;
    }
    
    setSelectedEvaluation(evaluation);
  };
  
  const handleInsightLevel = (level: '1' | '2' | '3' | '4' | '5') => {
    // 既に評価済みの場合は変更不可
    if (userEvaluation) {
      return;
    }
    
    setSelectedInsightLevel(level);
  };
  
  const handleSubmit = () => {
    if (!selectedEvaluation) {
      alert('革新性の評価を選択してください');
      return;
    }
    
    if (!selectedInsightLevel) {
      alert('示唆性の評価を選択してください');
      return;
    }
    
    onEvaluate(proposalId, selectedEvaluation, selectedInsightLevel);
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

  // 評価済みの場合の表示
  if (userEvaluation) {
    return (
      <div className="bg-gray-50 rounded-lg p-4 mb-4 border border-gray-300 space-y-4">
        <h4 className="text-sm font-medium text-gray-700 mb-3 text-center">【評価済み】</h4>
        
        {/* 革新性評価 */}
        <div>
          <p className="text-xs text-gray-600 mb-2 text-center">この結論を思い付いていましたか？</p>
          <div className="flex gap-2 justify-center">
            {(['no', 'maybe', 'yes'] as const).map((evaluation) => (
              <button
                key={evaluation}
                disabled={true}
                className={`
                  px-4 py-2 rounded-lg font-medium text-sm transition-colors duration-200
                  ${userEvaluation.evaluation === evaluation 
                    ? 'bg-gray-800 text-white'
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
        
        {/* 示唆性評価 */}
        {userEvaluation.insight_level && (
          <div>
            <p className="text-xs text-gray-600 mb-2 text-center">示唆に富んでいると感じますか？</p>
            <div className="flex gap-2 justify-center">
              {(['5', '4', '3', '2', '1'] as const).map((level) => (
                <button
                  key={level}
                  disabled={true}
                  className={`
                    px-3 py-2 rounded-lg font-medium text-sm transition-colors duration-200
                    ${userEvaluation.insight_level === level 
                      ? 'bg-gray-800 text-white'
                      : 'bg-gray-200 text-gray-400'
                    }
                    opacity-50 cursor-not-allowed
                  `}
                >
                  {level}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  // 評価未実施の場合
  return (
    <div className="bg-gray-50 rounded-lg p-4 mb-4 space-y-4">
      {/* 革新性評価 */}
      <div>
        <h4 className="text-sm font-medium text-gray-700 mb-2 text-center">この結論を思い付いていましたか？</h4>
        <div className="flex gap-2 justify-center">
          {(['no', 'maybe', 'yes'] as const).map((evaluation) => (
            <button
              key={evaluation}
              onClick={() => handleEvaluation(evaluation)}
              disabled={buttonDisabled}
              className={`
                px-4 py-2 rounded-lg font-medium text-sm transition-colors duration-200
                ${selectedEvaluation === evaluation 
                  ? 'bg-gray-800 hover:bg-gray-900 text-white'
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
      
      {/* 示唆性評価 */}
      <div>
        <h4 className="text-sm font-medium text-gray-700 mb-2 text-center">示唆に富んでいると感じますか？</h4>
        <div className="flex gap-2 justify-center">
          {(['5', '4', '3', '2', '1'] as const).map((level) => (
            <button
              key={level}
              onClick={() => handleInsightLevel(level)}
              disabled={buttonDisabled}
              className={`
                px-3 py-2 rounded-lg font-medium text-sm transition-colors duration-200
                ${selectedInsightLevel === level 
                  ? 'bg-gray-800 hover:bg-gray-900 text-white'
                  : 'bg-gray-200 hover:bg-gray-300 text-gray-700'
                }
                ${buttonDisabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
              `}
            >
              {level}
            </button>
          ))}
        </div>
      </div>
      
      {/* 送信ボタン */}
      <div className="flex justify-center pt-2">
        <button
          onClick={handleSubmit}
          disabled={buttonDisabled || !selectedEvaluation || !selectedInsightLevel}
          className={`
            px-6 py-2 rounded-lg font-medium text-sm transition-colors duration-200
            ${selectedEvaluation && selectedInsightLevel
              ? 'bg-gray-800 hover:bg-gray-900 text-white cursor-pointer'
              : 'bg-gray-300 text-gray-500 cursor-not-allowed'
            }
          `}
        >
          評価を送信
        </button>
      </div>
    </div>
  );
};

export default ProposalEvaluation;