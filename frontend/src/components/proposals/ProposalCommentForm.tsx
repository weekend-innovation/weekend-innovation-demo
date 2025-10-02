/**
 * 提案コメント作成フォームコンポーネント
 * 理由・推論過程へのコメントのみ許可
 */
import React, { useState } from 'react';
import type { ProposalCommentFormProps } from '../../types/proposal';

const ProposalCommentForm: React.FC<ProposalCommentFormProps> = ({
  onSubmit,
  isLoading = false
}) => {
  const [formData, setFormData] = useState({
    target_section: 'reasoning' as 'reasoning' | 'inference',
    conclusion: '',
    reasoning: ''
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // バリデーション
    const conclusion = formData.conclusion.trim();
    const reasoning = formData.reasoning.trim();
    
    if (conclusion.length < 10) {
      alert('結論は10文字以上で入力してください。');
      return;
    }
    
    if (reasoning.length < 20) {
      alert('理由は20文字以上で入力してください。');
      return;
    }
    
    onSubmit(formData);
    
    // フォームをリセット
    setFormData({
      target_section: 'reasoning',
      conclusion: '',
      reasoning: ''
    });
  };

  const handleChange = (field: keyof typeof formData, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  return (
    <div className="border rounded-lg p-4 bg-white">
      <h5 className="font-medium text-gray-900 mb-4">コメント投稿</h5>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* コメント対象選択 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            コメント対象
          </label>
          <div className="space-y-2 ml-4">
            <label className="flex items-center">
              <input
                type="radio"
                name="target_section"
                value="reasoning"
                checked={formData.target_section === 'reasoning'}
                onChange={(e) => handleChange('target_section', e.target.value as 'reasoning' | 'inference')}
                className="mr-2 text-blue-600 focus:ring-blue-500"
                disabled={isLoading}
              />
              <span className="text-sm text-gray-700">理由</span>
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                name="target_section"
                value="inference"
                checked={formData.target_section === 'inference'}
                onChange={(e) => handleChange('target_section', e.target.value as 'reasoning' | 'inference')}
                className="mr-2 text-blue-600 focus:ring-blue-500"
                disabled={isLoading}
              />
              <span className="text-sm text-gray-700">推論過程</span>
            </label>
          </div>
        </div>

        {/* 結論 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            結論 <span className="text-red-500">*</span>
          </label>
          <textarea
            value={formData.conclusion}
            onChange={(e) => handleChange('conclusion', e.target.value)}
            placeholder="コメントの結論を記述してください（10文字以上）"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            rows={3}
            maxLength={500}
            disabled={isLoading}
            required
          />
          <p className="text-xs text-gray-500 mt-1">
            {formData.conclusion.length}/500文字（最低10文字）
          </p>
        </div>

        {/* 理由 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            理由 <span className="text-red-500">*</span>
          </label>
          <textarea
            value={formData.reasoning}
            onChange={(e) => handleChange('reasoning', e.target.value)}
            placeholder="コメントの理由を詳しく記述してください（20文字以上）"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            rows={4}
            maxLength={1000}
            disabled={isLoading}
            required
          />
          <p className="text-xs text-gray-500 mt-1">
            {formData.reasoning.length}/1000文字（最低20文字）
          </p>
        </div>

        {/* ボタン */}
        <div className="pt-2">
          <button
            type="submit"
            disabled={isLoading || formData.conclusion.trim().length < 10 || formData.reasoning.trim().length < 20}
            className="w-full bg-gray-100 text-gray-700 px-4 py-2 rounded-lg border border-gray-300 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer transition-colors duration-200"
          >
            {isLoading ? '投稿中...' : 'コメントを投稿'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default ProposalCommentForm;