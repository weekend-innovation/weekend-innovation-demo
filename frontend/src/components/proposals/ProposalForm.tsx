/**
 * 提案フォームコンポーネント
 * 提案の作成・編集用フォーム
 * 結論と理由を分離して入力
 */
import React, { useState, useEffect } from 'react';
import type { ProposalFormProps, CreateProposalRequest, UpdateProposalRequest } from '@/types/proposal';

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
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
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
    } else if (formData.conclusion.trim().length < 10) {
      newErrors.conclusion = '結論は10文字以上で入力してください';
    } else if (formData.conclusion.length > 500) {
      newErrors.conclusion = '結論は500文字以内で入力してください';
    }

    if (!formData.reasoning.trim()) {
      newErrors.reasoning = '理由は必須です';
    } else if (formData.reasoning.trim().length < 20) {
      newErrors.reasoning = '理由は20文字以上で入力してください';
    } else if (formData.reasoning.length > 1000) {
      newErrors.reasoning = '理由は1000文字以内で入力してください';
    }

    setErrors(newErrors);
    
    // エラーがある場合はポップアップで表示
    if (Object.keys(newErrors).length > 0) {
      const errorMessages = Object.values(newErrors).join('\n');
      alert(errorMessages);
    }
    
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
          提案の結論を簡潔にまとめてください。（500文字以内）
        </p>
        <textarea
          id="conclusion"
          name="conclusion"
          value={formData.conclusion}
          onChange={handleChange}
          rows={4}
          maxLength={500}
          className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            errors.conclusion ? 'border-red-500' : 'border-gray-300'
          }`}
          placeholder="提案の結論を入力してください"
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
          理由を詳しく説明してください。（1000文字以内）
        </p>
        <textarea
          id="reasoning"
          name="reasoning"
          value={formData.reasoning}
          onChange={handleChange}
          rows={6}
          maxLength={1000}
          className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            errors.reasoning ? 'border-red-500' : 'border-gray-300'
          }`}
          placeholder="提案の理由を入力してください"
        />
        {errors.reasoning && (
          <p className="mt-1 text-sm text-red-600">{errors.reasoning}</p>
        )}
        <p className="mt-1 text-sm text-gray-500">
          {formData.reasoning.length}/1000文字
        </p>
      </div>

      {/* ヒントセクション */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="text-base font-medium text-blue-900 mb-2">
          提案について
        </h3>
        <p className="text-base text-blue-800">
          大量の解決案を評価する必要があるため、簡潔に表現することが望ましいです。
        </p>
      </div>

      {/* 送信ボタン */}
      <div className="flex justify-end pt-6 border-t border-gray-200">
        <button
          type="submit"
          disabled={isLoading}
          className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
        >
          {isLoading ? '処理中...' : mode === 'create' ? '解決案を提案' : '更新'}
        </button>
      </div>
    </form>
  );
};

export default ProposalForm;
