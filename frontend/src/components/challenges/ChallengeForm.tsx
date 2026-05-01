/**
 * 課題フォームコンポーネント
 * 課題の作成・編集用フォーム
 */
import React, { useState, useEffect } from 'react';
import type { ChallengeFormProps, CreateChallengeRequest } from '../../types/challenge';
import { DemoRewardAmountPlaceholder } from '../common/DemoRewardDisclaimer';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api';

/** バックエンド mvp_project.limits.MAX_SELECTION_PARTICIPANTS と揃える */
const MAX_SELECTION_PARTICIPANTS = 700;

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
        reward_amount: initialData.reward_amount || 0,
        adoption_reward: initialData.adoption_reward || 50,
        required_participants: participants,
        deadline: initialData.deadline || ''
      });
    } else if (mode === 'create') {
      // 新規作成時は初期値で提案報酬を計算
      calculateRewardAmount(50);
    }
  }, [initialData, mode]);
  
  // 提案報酬を計算する関数
  const calculateRewardAmount = async (participants: number) => {
    if (participants < 50 || participants > MAX_SELECTION_PARTICIPANTS) {
      // エラー範囲の場合は報酬を無効値に設定
      setFormData(prev => ({ ...prev, reward_amount: -1 }));
      return;
    }
    
    try {
      const response = await fetch(`${API_BASE_URL}/challenges/calculate-reward/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({ required_participants: participants })
      });
      
      if (response.ok) {
        const data = await response.json();
        setFormData(prev => ({ ...prev, reward_amount: data.reward_amount_man }));
      }
    } catch (error) {
      console.error('提案報酬計算エラー:', error);
    }
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

    const participants = name === 'required_participants' && processedValue !== '' 
      ? (Number(processedValue) || 0) 
      : null;
    
    // 選出人数の場合、報酬を先に設定
    let rewardAmount = formData.reward_amount;
    if (mode === 'create' && name === 'required_participants' && participants !== null) {
      if (participants < 50 || participants > MAX_SELECTION_PARTICIPANTS) {
        // エラー範囲の場合は報酬を無効値に設定
        rewardAmount = -1;
      }
    }
    
    const newFormData = {
      ...formData,
      [name]: name.includes('_amount') || name === 'required_participants' 
        ? (processedValue === '' ? 0 : Number(processedValue) || 0)
        : processedValue,
      reward_amount: rewardAmount
    };

    setFormData(newFormData);
    
    // 新規作成モードで選出人数が変更された場合、提案報酬を再計算
    if (mode === 'create' && name === 'required_participants') {
      // リアルタイムバリデーション（必須エラーは表示しない）
      const newErrors = { ...errors };
      
      // 空白の場合はエラー状態をクリア（必須エラーは投稿時にのみ表示）
      if (processedValue === '' || participants === null || participants === 0) {
        delete newErrors.required_participants;
        // 報酬を無効値に設定
        setFormData(prev => ({ ...prev, reward_amount: -1 }));
      } else if (participants! < 50) {
        // エラー状態を設定（メッセージは表示しない）
        newErrors.required_participants = 'invalid_min';
        // 報酬を無効値に設定
        setFormData(prev => ({ ...prev, reward_amount: -1 }));
      } else if (participants! > MAX_SELECTION_PARTICIPANTS) {
        // エラー状態を設定（メッセージは表示しない）
        newErrors.required_participants = 'invalid_max';
        // 報酬を無効値に設定
        setFormData(prev => ({ ...prev, reward_amount: -1 }));
      } else {
        delete newErrors.required_participants;
        // 正常範囲内の場合は報酬を計算
        // reward_amountが-1の場合はリセットしてから計算
        if (formData.reward_amount === -1) {
          setFormData(prev => ({ ...prev, reward_amount: 0 }));
        }
        calculateRewardAmount(participants!);
      }
      setErrors(newErrors);
    } else {
      // その他のフィールドのエラーをクリア
      if (errors[name]) {
        setErrors(prev => ({ ...prev, [name]: '' }));
      }
    }
  };

  // バリデーション
  const validateForm = (): { isValid: boolean; errors: Record<string, string> } => {
    const newErrors: Record<string, string> = {};

    if (!formData.title.trim()) {
      newErrors.title = '課題タイトルは必須です';
    } else if (formData.title.length > 200) {
      newErrors.title = '課題タイトルは200文字以内で入力してください';
    }

    if (!formData.description.trim()) {
      newErrors.description = '課題内容は必須です';
    }

    // 編集モードでは報酬・選出人数・期限のバリデーションをスキップ
    if (mode === 'create') {
      // 提案報酬は自動計算のためバリデーション不要

      if (formData.adoption_reward <= 0) {
        newErrors.adoption_reward = '採用報酬は0円より大きい必要があります';
      }

      // 選出人数のバリデーション（選出人数が適正か否かにかかわらずチェック）
      if (!formData.required_participants || formData.required_participants === 0) {
        // 空白または0の場合は必須エラー
        newErrors.required_participants = '選出人数は必須です';
        // 報酬を無効値に設定
        if (formData.reward_amount !== -1) {
          setFormData(prev => ({ ...prev, reward_amount: -1 }));
        }
      } else if (formData.required_participants < 50) {
        // エラー状態を設定（メッセージは表示しない）
        newErrors.required_participants = 'invalid_min';
        // 報酬を無効値に設定
        if (formData.reward_amount !== -1) {
          setFormData(prev => ({ ...prev, reward_amount: -1 }));
        }
      } else if (formData.required_participants > MAX_SELECTION_PARTICIPANTS) {
        // エラー状態を設定（メッセージは表示しない）
        newErrors.required_participants = 'invalid_max';
        // 報酬を無効値に設定
        if (formData.reward_amount !== -1) {
          setFormData(prev => ({ ...prev, reward_amount: -1 }));
        }
      }

      // 期限のバリデーション（最低6日必要: 提案3日、編集1日、評価2日）
      const MIN_TOTAL_DAYS = 6;
      if (!formData.deadline) {
        newErrors.deadline = '期限は必須です';
      } else {
        const deadlineDate = new Date(formData.deadline);
        const now = new Date();
        if (deadlineDate <= now) {
          newErrors.deadline = '期限は現在時刻より後の日時である必要があります';
        } else {
          const diffMs = deadlineDate.getTime() - now.getTime();
          const totalDays = Math.floor(diffMs / (24 * 60 * 60 * 1000));
          if (totalDays < MIN_TOTAL_DAYS) {
            newErrors.deadline = `期限まで最低${MIN_TOTAL_DAYS}日必要です`;
          }
        }
      }
    }

    setErrors(newErrors);
    return { isValid: Object.keys(newErrors).length === 0, errors: newErrors };
  };

  // フォーム送信処理
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // バリデーションを実行
    const validationResult = validateForm();
    
    // バリデーションエラーがある場合は送信しない
    if (!validationResult.isValid) {
      // validateForm()で設定されたエラーを直接確認
      const validationErrors = validationResult.errors;
      
      // 選出人数のエラーがある場合は適切なメッセージを表示
      // 必須エラーの場合は枠下に表示されているので、ポップアップは表示しない（期限欄と同じ）
      if (validationErrors.required_participants === 'invalid_min') {
        alert('選出人数は50人以上にする必要があります。');
      } else if (validationErrors.required_participants === 'invalid_max') {
        alert(`選出人数は${MAX_SELECTION_PARTICIPANTS}人以下にする必要があります。`);
      }
      // 必須エラー（'選出人数は必須です'）の場合はポップアップを表示しない
      
      return;
    }
    
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6" noValidate>
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

      {/* 編集モードでは報酬・選出人数・期限は編集不可（表示のみ） */}
      {mode === 'edit' ? (
        <>
          {/* 報酬設定（表示のみ） */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                提案報酬（万円）
              </label>
              <input
                type="text"
                value={formData.reward_amount}
                readOnly
                className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100 text-gray-600 cursor-not-allowed"
              />
              <p className="mt-1 text-sm text-gray-500">
                報酬は編集できません
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                採用報酬（万円）
              </label>
              <input
                type="text"
                value={formData.adoption_reward}
                readOnly
                className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100 text-gray-600 cursor-not-allowed"
              />
              <p className="mt-1 text-sm text-gray-500">
                報酬は編集できません
              </p>
            </div>
          </div>

          {/* 選出人数と期限（表示のみ） */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                選出人数
              </label>
              <input
                type="text"
                value={formData.required_participants}
                readOnly
                className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100 text-gray-600 cursor-not-allowed"
              />
              <p className="mt-1 text-sm text-gray-500">
                選出人数は編集できません
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                期限
              </label>
              <input
                type="text"
                value={formData.deadline ? new Date(formData.deadline).toLocaleDateString('ja-JP') : ''}
                readOnly
                className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100 text-gray-600 cursor-not-allowed"
              />
              <p className="mt-1 text-sm text-gray-500">
                期限は編集できません
              </p>
            </div>
          </div>
        </>
      ) : (
        <>
          {/* 報酬設定 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                提案報酬総額（万円） <span className="text-gray-500 text-sm">（自動計算）</span>
              </label>
              <div className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-blue-50 text-blue-900 font-medium text-lg">
                <DemoRewardAmountPlaceholder className="text-blue-900 font-medium text-lg" />
              </div>
              <p className="mt-1 text-sm text-gray-500">
                デモ版では報酬金額は表示されません
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                採用報酬（万円） <span className="text-red-500">*</span>
              </label>
              <div className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-green-50 text-green-900 font-medium text-lg">
                <DemoRewardAmountPlaceholder className="text-green-900 font-medium text-lg" />
              </div>
              {errors.adoption_reward && (
                <p className="mt-1 text-sm text-red-600">{errors.adoption_reward}</p>
              )}
              <p className="mt-1 text-sm text-gray-500">
                デモ版では報酬金額は表示されません
              </p>
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
                max={MAX_SELECTION_PARTICIPANTS}
                step="1"
                className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none [-moz-appearance:textfield] ${
                  errors.required_participants ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="50"
              />
              {/* エラーメッセージを表示（期限欄と同じように、投稿時にのみ表示） */}
              {errors.required_participants && errors.required_participants !== 'invalid_min' && errors.required_participants !== 'invalid_max' && (
                <p className="mt-1 text-sm text-red-600">{errors.required_participants}</p>
              )}
              <p className="mt-1 text-sm text-gray-500">
                50人〜{MAX_SELECTION_PARTICIPANTS}人まで設定可能です
              </p>
            </div>

            <div>
              <label htmlFor="deadline" className="block text-sm font-medium text-gray-700 mb-2">
                期限 <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <input
                  type="date"
                  id="deadline"
                  name="deadline"
                  value={formData.deadline ? formData.deadline.split('T')[0] : ''}
                  onChange={(e) => {
                    const selectedDate = e.target.value;
                    if (selectedDate) {
                      const deadlineWithTime = `${selectedDate}T23:59`;
                      setFormData(prev => ({
                        ...prev,
                        deadline: deadlineWithTime
                      }));
                    } else {
                      setFormData(prev => ({
                        ...prev,
                        deadline: ''
                      }));
                    }
                  }}
                  min={(() => {
                    const d = new Date();
                    d.setDate(d.getDate() + 6);
                    return d.toISOString().split('T')[0];
                  })()}
                  className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    errors.deadline ? 'border-red-500' : 'border-gray-300'
                  }`}
                  style={{ colorScheme: 'light' }}
                />
                {formData.deadline && (
                  <div className="absolute left-3 top-1/2 transform -translate-y-1/2 pointer-events-none bg-white px-1">
                    <span className="text-gray-700">
                      {formData.deadline.split('T')[0].replace(/-/g, '/')} 23:59
                    </span>
                  </div>
                )}
              </div>
              {errors.deadline && (
                <p className="mt-1 text-sm text-red-600">{errors.deadline}</p>
              )}
              <p className="mt-1 text-sm text-gray-500">
                期限まで最低6日必要です
              </p>
            </div>
          </div>
        </>
      )}

      {/* 送信ボタン */}
      <div className="flex justify-end gap-4 pt-6 border-t border-gray-200">
        <button
          type="button"
          onClick={() => window.history.back()}
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
