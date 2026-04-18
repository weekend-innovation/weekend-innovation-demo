/**
 * 解決案編集フォームコンポーネント
 * コメントを参考にして解決案を編集する
 */
import React, { useState } from 'react';
import type { ProposalListItem } from '../../types/proposal';

interface ProposalEditFormProps {
  proposal: ProposalListItem;
  referenceCommentId: number;
  onSubmit: (proposalId: number, data: { conclusion: string; reasoning: string }) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

const ProposalEditForm: React.FC<ProposalEditFormProps> = ({
  proposal,
  onSubmit,
  onCancel,
  isLoading = false
}) => {
  const [conclusion, setConclusion] = useState(proposal.conclusion || '');
  const [reasoning, setReasoning] = useState(proposal.reasoning || '');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (conclusion.trim() && reasoning.trim()) {
      onSubmit(proposal.id, {
        conclusion: conclusion.trim(),
        reasoning: reasoning.trim()
      });
    }
  };

  return (
    <div className="border-l-4 border-green-200 pl-4 mt-3">
      <div className="group relative mb-3">
        <h6 className="font-medium text-gray-800 cursor-help">【参考】</h6>
        <div className="absolute bottom-full left-0 mb-2 hidden group-hover:block bg-gray-800 text-white text-xs rounded py-1 px-2 whitespace-nowrap z-10">
            コメントを参考にしてあなたの解決案の結論や理由を編集できます
        </div>
      </div>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">結論</label>
          <textarea
            value={conclusion}
            onChange={(e) => setConclusion(e.target.value)}
            placeholder="結論を入力してください"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500"
            rows={3}
            maxLength={500}
            disabled={isLoading}
            required
          />
          <p className="text-xs text-gray-500 mt-1">
            {conclusion.length}/500文字
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">理由</label>
          <textarea
            value={reasoning}
            onChange={(e) => setReasoning(e.target.value)}
            placeholder="理由を入力してください"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500"
            rows={5}
            maxLength={1000}
            disabled={isLoading}
            required
          />
          <p className="text-xs text-gray-500 mt-1">
            {reasoning.length}/1000文字
          </p>
        </div>

        <div className="flex justify-end gap-2">
          <button
            type="submit"
            disabled={isLoading || !conclusion.trim() || !reasoning.trim()}
            className="bg-green-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200 font-medium shadow-sm hover:shadow-md cursor-pointer"
          >
            {isLoading ? '編集中...' : '編集'}
          </button>
          <button
            type="button"
            onClick={onCancel}
            disabled={isLoading}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg text-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200 font-medium cursor-pointer"
          >
            閉じる
          </button>
        </div>
      </form>
    </div>
  );
};

export default ProposalEditForm;
