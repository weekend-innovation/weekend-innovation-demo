/**
 * 課題フォームコンポーネント
 * 課題の作成・編集用フォーム
 */
import React, { useState, useEffect } from 'react';
import type { ChallengeFormProps, CreateChallengeRequest, UpdateChallengeRequest } from '../../types/challenge';

const ChallengeForm: React.FC<ChallengeFormProps> = ({
  initialData,
  onSubmit,
  isLoading = false,
  mode
}) => {
  // フォームの状態管理
  const [formData, setFormData] = useState<CreateChallengeRequest>({
    title: '',
    description: '',
    reward_amount: 0,
    adoption_reward: 50,
    required_participants: 50,
    deadline: ''
  });

  // バリデーションエラー
  const [errors, setErrors] = useState<Record<string, string>>({});

  // 初期データの設定
  useEffect(() => {
    if (initialData && mode === 'edit') {
      const participants = initialData.required_participants || 50;
      setFormData({
        title: initialData.title || '',
        description: initialData.description || '',
        reward_amount: initialData.reward_amount || calculateProposalReward(participants),
        adoption_reward: initialData.adoption_reward || 50,
        required_participants: participants,
        deadline: initialData.deadline || ''
      });
    } else if (mode === 'create') {
      // 新規作成時は提案報酬を自動計算
      setFormData(prev => ({
        ...prev,
        reward_amount: calculateProposalReward(prev.required_participants)
      }));
    }
  }, [initialData, mode]);

  // 提案報酬の自動計算
  const calculateProposalReward = (participants: number): number => {
    // 選出人数×1万円 + 選出人数×雑費（1人あたり5,000円と仮定）
    const baseReward = participants * 10000; // 1万円×選出人数
    const miscellaneousFees = participants * 5000; // 雑費（サーバー利用料等）
    return baseReward + miscellaneousFees;
  };

  // 入力値の変更処理
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    let processedValue = value;

    // 選出人数の特別処理
    if (name === 'required_participants') {
      // 先頭の0を削除（空文字列の場合は空文字列を保持）
      if (value === '') {
        processedValue = '';
      } else {
        // 先頭の0を削除し、空文字列になった場合は空文字列を保持
        processedValue = value.replace(/^0+/, '');
        if (processedValue === '') {
          processedValue = '';
        }
      }
    }

    const newFormData = {
      ...formData,
      [name]: name.includes('_amount') || name === 'required_participants' 
        ? (processedValue === '' ? 0 : Number(processedValue) || 0)
        : processedValue
    };

    // 選出人数が変更された場合、提案報酬を自動計算
    if (name === 'required_participants') {
      const participants = processedValue === '' ? 0 : Number(processedValue) || 0;
      newFormData.reward_amount = calculateProposalReward(participants);
    }

    setFormData(newFormData);
    
    // エラーをクリア
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  // バリデーション
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.title.trim()) {
      newErrors.title = '課題タイトルは必須です';
    } else if (formData.title.length > 200) {
      newErrors.title = '課題タイトルは200文字以内で入力してください';
    }

    if (!formData.description.trim()) {
      newErrors.description = '課題内容は必須です';
    }

    // 提案報酬は自動計算のためバリデーション不要

    if (formData.adoption_reward <= 0) {
      newErrors.adoption_reward = '採用報酬は0円より大きい必要があります';
    }

    if (formData.required_participants < 50) {
      alert('選出人数は50人以上である必要があります。');
      newErrors.required_participants = '選出人数は50人以上である必要があります';
    }

    if (!formData.deadline) {
      newErrors.deadline = '期限は必須です';
    } else {
      const deadlineDate = new Date(formData.deadline);
      const now = new Date();
      if (deadlineDate <= now) {
        newErrors.deadline = '期限は現在時刻より後の日時である必要があります';
      }
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

  // 期限の最小値を現在時刻に設定
  const minDateTime = new Date().toISOString().slice(0, 16);

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* 課題タイトル */}
      <div>
        <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
          課題タイトル <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          id="title"
          name="title"
          value={formData.title}
          onChange={handleChange}
          className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            errors.title ? 'border-red-500' : 'border-gray-300'
          }`}
          placeholder="課題のタイトルを入力してください"
          maxLength={200}
        />
        {errors.title && (
          <p className="mt-1 text-sm text-red-600">{errors.title}</p>
        )}
      </div>

      {/* 課題内容 */}
      <div>
        <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
          課題内容 <span className="text-red-500">*</span>
        </label>
        <textarea
          id="description"
          name="description"
          value={formData.description}
          onChange={handleChange}
          rows={6}
          className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            errors.description ? 'border-red-500' : 'border-gray-300'
          }`}
          placeholder="課題の詳細内容を入力してください"
        />
        {errors.description && (
          <p className="mt-1 text-sm text-red-600">{errors.description}</p>
        )}
      </div>

      {/* 報酬設定 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label htmlFor="reward_amount" className="block text-sm font-medium text-gray-700 mb-2">
            提案報酬（円） <span className="text-gray-500 text-sm">（自動計算）</span>
          </label>
          <input
            type="number"
            id="reward_amount"
            name="reward_amount"
            value={formData.reward_amount}
            readOnly
            className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-600"
            placeholder="0"
          />
        </div>

        <div>
          <label htmlFor="adoption_reward" className="block text-sm font-medium text-gray-700 mb-2">
            採用報酬（万円） <span className="text-red-500">*</span>
          </label>
          <input
            type="number"
            id="adoption_reward"
            name="adoption_reward"
            value={formData.adoption_reward}
            onChange={handleChange}
            min="1"
            step="1"
            className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none [-moz-appearance:textfield] ${
              errors.adoption_reward ? 'border-red-500' : 'border-gray-300'
            }`}
            placeholder="50"
          />
          {errors.adoption_reward && (
            <p className="mt-1 text-sm text-red-600">{errors.adoption_reward}</p>
          )}
        </div>
      </div>

      {/* 選出人数と期限 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label htmlFor="required_participants" className="block text-sm font-medium text-gray-700 mb-2">
            選出人数 <span className="text-red-500">*</span>
          </label>
          <input
            type="number"
            id="required_participants"
            name="required_participants"
            value={formData.required_participants === 0 ? '' : formData.required_participants}
            onChange={handleChange}
            min="50"
            step="1"
            className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none [-moz-appearance:textfield] ${
              errors.required_participants ? 'border-red-500' : 'border-gray-300'
            }`}
            placeholder="50"
          />
          {errors.required_participants && (
            <p className="mt-1 text-sm text-red-600">{errors.required_participants}</p>
          )}
          <p className="mt-1 text-sm text-gray-500">
            最低50人から設定可能です
          </p>
        </div>

        <div>
          <label htmlFor="deadline" className="block text-sm font-medium text-gray-700 mb-2">
            期限 <span className="text-red-500">*</span>
          </label>
          <input
            type="datetime-local"
            id="deadline"
            name="deadline"
            value={formData.deadline}
            onChange={handleChange}
            min={minDateTime}
            className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.deadline ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.deadline && (
            <p className="mt-1 text-sm text-red-600">{errors.deadline}</p>
          )}
        </div>
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
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
        >
          {isLoading ? '処理中...' : mode === 'create' ? '課題を投稿' : '更新'}
        </button>
      </div>
    </form>
  );
};

export default ChallengeForm;
