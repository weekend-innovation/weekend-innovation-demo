/**
 * 分析結果・解決案一覧の切り替えスイッチコンポーネント
 */
import React from 'react';

interface AnalysisToggleSwitchProps {
  showAnalysis: boolean;
  onToggle: (showAnalysis: boolean) => void;
  isLoading?: boolean;
}

const AnalysisToggleSwitch: React.FC<AnalysisToggleSwitchProps> = ({
  showAnalysis,
  onToggle,
  isLoading = false
}) => {
  return (
    <div className="relative">
      <button
        type="button"
        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
          showAnalysis ? 'bg-blue-600' : 'bg-gray-200'
        } ${isLoading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
        onClick={() => !isLoading && onToggle(!showAnalysis)}
        disabled={isLoading}
        role="switch"
        aria-checked={showAnalysis}
        aria-label={showAnalysis ? '分析結果を表示中' : '解決案一覧を表示中'}
      >
        <span
          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
            showAnalysis ? 'translate-x-6' : 'translate-x-1'
          }`}
        />
      </button>
    </div>
  );
};

export default AnalysisToggleSwitch;
