/**
 * 提案フォームコンポーネント
 * 提案の作成・編集用フォーム
 * 結論と理由を分離して入力
 */
import React, { useState, useEffect } from 'react';
import type { ProposalFormProps, CreateProposalRequest, UpdateProposalRequest } from '../../types/proposal';

const ProposalForm: React.FC<ProposalFormProps> = ({
  challengeId,
  initialData,
  onSubmit,
  isLoading = false,
  mode
}) => {
  // フォームの状態管理
  const [formData, setFormData] = useState<CreateProposalRequest>({
    challenge: challengeId,
    conclusion: '',
    reasoning: ''
  });

  // バリデーションエラー
  const [errors, setErrors] = useState<Record<string, string>>({});

  // 初期データの設定
  useEffect(() => {
    if (initialData && mode === 'edit') {
      setFormData({
        challenge: challengeId,
        conclusion: initialData.conclusion || '',
        reasoning: initialData.reasoning || ''
      });
    }
  }, [initialData, mode, challengeId]);

  // 入力値の変更処理
  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // エラーをクリア
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  // バリデーション
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.conclusion.trim()) {
      newErrors.conclusion = '結論は必須です';
    } else if (formData.conclusion.length < 10) {
      newErrors.conclusion = '結論は10文字以上で入力してください';
    }

    if (!formData.reasoning.trim()) {
      newErrors.reasoning = '理由は必須です';
    } else if (formData.reasoning.length < 20) {
      newErrors.reasoning = '理由は20文字以上で入力してください';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // フォーム送信処理
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (validateForm()) {
      onSubmit(formData);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* 結論セクション */}
      <div>
        <label htmlFor="conclusion" className="block text-sm font-medium text-gray-700 mb-2">
          結論 <span className="text-red-500">*</span>
        </label>
        <p className="text-sm text-gray-600 mb-3">
          あなたの提案の結論を簡潔にまとめてください。
        </p>
        <textarea
          id="conclusion"
          name="conclusion"
          value={formData.conclusion}
          onChange={handleChange}
          rows={4}
          className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            errors.conclusion ? 'border-red-500' : 'border-gray-300'
          }`}
          placeholder="例: この課題を解決するために、AIを活用した自動化システムを導入することを提案します。"
        />
        {errors.conclusion && (
          <p className="mt-1 text-sm text-red-600">{errors.conclusion}</p>
        )}
        <p className="mt-1 text-sm text-gray-500">
          {formData.conclusion.length}/500文字
        </p>
      </div>

      {/* 理由セクション */}
      <div>
        <label htmlFor="reasoning" className="block text-sm font-medium text-gray-700 mb-2">
          理由 <span className="text-red-500">*</span>
        </label>
        <p className="text-sm text-gray-600 mb-3">
          なぜその結論に至ったのか、その理由と根拠を詳しく説明してください。
        </p>
        <textarea
          id="reasoning"
          name="reasoning"
          value={formData.reasoning}
          onChange={handleChange}
          rows={8}
          className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            errors.reasoning ? 'border-red-500' : 'border-gray-300'
          }`}
          placeholder="例: 現在の手作業による処理では時間がかかり、人的ミスも発生しやすい状況です。AIを活用することで、処理時間を80%短縮し、精度を95%以上に向上させることができます。また、既存のシステムとの連携も容易で、導入コストも抑えられます。"
        />
        {errors.reasoning && (
          <p className="mt-1 text-sm text-red-600">{errors.reasoning}</p>
        )}
        <p className="mt-1 text-sm text-gray-500">
          {formData.reasoning.length}/2000文字
        </p>
      </div>

      {/* ヒントセクション */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="text-sm font-medium text-blue-900 mb-2">
          効果的な提案のコツ
        </h3>
        <ul className="space-y-1 text-sm text-blue-800">
          <li className="flex items-start gap-2">
            <span className="text-blue-600 mt-1">•</span>
            <span>結論は具体的で実現可能な内容にしてください</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blue-600 mt-1">•</span>
            <span>理由では根拠となるデータや事例を挙げてください</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blue-600 mt-1">•</span>
            <span>課題の背景を理解し、解決策の効果を明確に示してください</span>
          </li>
        </ul>
      </div>

      {/* 送信ボタン */}
      <div className="flex justify-end gap-4 pt-6 border-t border-gray-200">
        <button
          type="button"
          className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors duration-200"
          disabled={isLoading}
        >
          キャンセル
        </button>
        <button
          type="submit"
          disabled={isLoading}
          className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
        >
          {isLoading ? '処理中...' : mode === 'create' ? '提案を投稿' : '更新'}
        </button>
      </div>
    </form>
  );
};

export default ProposalForm;
