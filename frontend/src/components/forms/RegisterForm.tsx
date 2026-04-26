/**
 * 新規登録フォームコンポーネント
 * Weekend Innovationプロジェクトの新規登録機能
 * 
 * Phase 1実装内容:
 * - 3ステップの登録フロー（ユーザータイプ選択→基本情報→プロフィール）
 * - 投稿者・提案者の2つのユーザータイプ対応
 * - ユーザータイプ別プロフィール入力フォーム
 * - バリデーション・エラーハンドリング
 * - 登録成功時のダッシュボードリダイレクト
 * - ログインページへのリンク
 * - ホームページへの戻るボタン
 */

'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { authAPI, ApiError, mapDrfErrorBodyToFieldErrors } from '@/lib/api';
import { RegisterRequest, UserType } from '@/types/auth';

type RegisterFormData = Omit<RegisterRequest, 'profile'> & {
  profile: Record<string, string | undefined>;
};

export function RegisterForm() {
  const { applyAuthResponse } = useAuth();
  const [step, setStep] = useState<'user-type' | 'user-info' | 'profile'>('user-type');
  const [userType, setUserType] = useState<UserType | null>(null);
  const [formData, setFormData] = useState<RegisterFormData>({
    username: '',
    email: '',
    password: '',
    password_confirm: '',
    user_type: 'contributor',
    profile: {},
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isCheckingUserInfo, setIsCheckingUserInfo] = useState(false);
  const [error, setError] = useState<string>('');
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const router = useRouter();

  const inputErrorClass = (name: string) =>
    fieldErrors[name] ? ' border-red-500 focus:border-red-500 focus:ring-red-200' : '';

  const handleUserTypeSelect = (type: UserType) => {
    setUserType(type);
    setFormData(prev => ({
      ...prev,
      user_type: type,
      profile: type === 'contributor' ? {
        company_name: '',
        representative_name: '',
        address: '',
        phone_number: '',
        industry: '',
      } : {
        full_name: '',
        gender: '',
        birth_date: '',
        address: '',
        phone_number: '',
      },
    }));
    setStep('user-info');
  };

  const handleUserInfoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
    if (error) setError('');
    if (name) {
      setFieldErrors((prev) => {
        const n = { ...prev };
        delete n[name];
        delete n._form;
        return n;
      });
    }
  };

  const handleProfileChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      profile: {
        ...prev.profile,
        [name]: value,
      },
    }));
    if (error) setError('');
    if (name) {
      setFieldErrors((prev) => {
        const n = { ...prev };
        delete n[name];
        return n;
      });
    }
  };

  const validateBasicInfo = (): boolean => {
    const fe: Record<string, string> = {};
    if (!formData.username.trim()) {
      fe.username = 'ユーザー名を入力してください';
    }
    if (!formData.email.trim()) {
      fe.email = 'メールアドレスを入力してください';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email.trim())) {
      fe.email = '有効なメールアドレスの形式で入力してください';
    }
    if (!formData.password) {
      fe.password = 'パスワードを入力してください';
    } else if (formData.password.length < 8) {
      fe.password = 'パスワードは8文字以上にしてください';
    }
    if (formData.password !== formData.password_confirm) {
      fe.password_confirm = 'パスワードとパスワード確認が一致しません';
    }
    if (Object.keys(fe).length) {
      setFieldErrors(fe);
      return false;
    }
    return true;
  };

  const validateProfileStep = (): boolean => {
    if (!userType) {
      return false;
    }
    const fe: Record<string, string> = {};
    if (userType === 'contributor') {
      if (!formData.profile.company_name?.trim()) {
        fe.company_name = '商号を入力してください';
      }
      if (!formData.profile.representative_name?.trim()) {
        fe.representative_name = '担当者名を入力してください';
      }
      if (!formData.profile.address?.trim()) {
        fe.address = '住所を入力してください';
      }
      if (!formData.profile.phone_number?.trim()) {
        fe.phone_number = '電話番号を入力してください';
      }
    }
    if (Object.keys(fe).length) {
      setFieldErrors((prev) => ({ ...prev, ...fe }));
      return false;
    }
    return true;
  };

  const handleUserInfoNext = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setFieldErrors((prev) => {
      const n = { ...prev };
      for (const k of ['username', 'email', 'password', 'password_confirm', '_form'] as const) {
        delete n[k];
      }
      return n;
    });
    if (!validateBasicInfo()) {
      return;
    }
    setIsCheckingUserInfo(true);
    try {
      const r = await authAPI.checkRegistrationAvailability(
        formData.email,
        formData.username
      );
      const fe: Record<string, string> = {};
      if (!r.email_available) {
        // メール存在の有無を断定しない（ユーザ列挙の抑止）
        fe.email =
          '入力内容をご確認のうえ、再度お試しください。登録がお済みの場合はログイン画面をご利用ください。';
      }
      if (!r.username_available) {
        fe.username = 'このユーザー名は既に使われています。別のユーザー名にしてください。';
      }
      if (Object.keys(fe).length) {
        setFieldErrors(fe);
        return;
      }
      setStep('profile');
    } catch (err) {
      setError(err instanceof Error ? err.message : '利用可否の確認に失敗しました');
    } finally {
      setIsCheckingUserInfo(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateProfileStep()) {
      return;
    }
    setIsLoading(true);
    setError('');
    setFieldErrors({});

    try {
      const response = await authAPI.register(formData as unknown as RegisterRequest);
      // トークンは api 層で保存済み。ヘッダー等は user を見るためコンテキストも同期する
      applyAuthResponse(response);

      // 登録成功後、ユーザータイプに応じてリダイレクト
      if (response.user.user_type === 'contributor') {
        router.push('/dashboard/contributor');
      } else {
        router.push('/dashboard/proposer');
      }
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setError(err.message);
        setFieldErrors(mapDrfErrorBodyToFieldErrors(err.body));
        return;
      }
      setError(err instanceof Error ? err.message : '登録に失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  const renderUserTypeSelection = () => (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-3xl font-extrabold text-gray-900">ユーザータイプを選択</h2>
        <p className="mt-2 text-sm text-gray-600">
          あなたのユーザータイプを選択してください
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4">
        <button
          onClick={() => handleUserTypeSelect('contributor')}
          className="relative p-6 border-2 border-gray-200 rounded-lg hover:border-black transition-colors text-left cursor-pointer"
        >
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
              </div>
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-medium text-gray-900">投稿者</h3>
              <p className="text-sm text-gray-500">
                創出に繋がる課題を投稿します
              </p>
            </div>
          </div>
        </button>

        <button
          onClick={() => handleUserTypeSelect('proposer')}
          className="relative p-6 border-2 border-gray-200 rounded-lg hover:border-black transition-colors text-left cursor-pointer"
        >
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-medium text-gray-900">提案者</h3>
              <p className="text-sm text-gray-500">
                課題に対する解決案を提案します
              </p>
            </div>
          </div>
        </button>
      </div>
    </div>
  );

  const renderUserInfoForm = () => (
    <div className="space-y-6">
      <div className="text-center">
        <button
          onClick={() => setStep('user-type')}
          className="text-sm text-gray-600 hover:text-black cursor-pointer"
        >
          ← 戻る
        </button>
        <h2 className="mt-4 text-3xl font-extrabold text-gray-900">基本情報</h2>
      </div>

      <form onSubmit={handleUserInfoNext} className="space-y-4" noValidate>
        <div>
          <label htmlFor="username" className="block text-sm font-medium text-gray-700">
            ユーザー名
          </label>
          <input
            id="username"
            name="username"
            type="text"
            autoComplete="username"
            value={formData.username}
            onChange={handleUserInfoChange}
            className={
              'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-black focus:border-black' +
              inputErrorClass('username')
            }
            placeholder="ユーザー名"
          />
          {fieldErrors.username && (
            <p className="mt-1 text-xs text-red-600 leading-relaxed">
              {fieldErrors.username}
            </p>
          )}
        </div>

        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-700">
            メールアドレス *
          </label>
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            value={formData.email}
            onChange={handleUserInfoChange}
            className={
              'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-black focus:border-black' +
              inputErrorClass('email')
            }
            placeholder="your@email.com"
          />
          {fieldErrors.email && (
            <p className="mt-1 text-sm text-red-600">{fieldErrors.email}</p>
          )}
          {userType === 'proposer' && (
            <p className="mt-1 pl-3 text-xs text-gray-500 border-l-2 border-gray-200">
              デモ版ではランダムに選出された際に通知するためのものであるため、実在しないメールアドレスでも登録できます（確認メール認証は行いません）。
            </p>
          )}
        </div>

        <div>
          <label htmlFor="password" className="block text-sm font-medium text-gray-700">
            パスワード
          </label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="new-password"
            value={formData.password}
            onChange={handleUserInfoChange}
            className={
              'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-black focus:border-black' +
              inputErrorClass('password')
            }
            placeholder="パスワード（8文字以上）"
          />
          {fieldErrors.password && (
            <p className="mt-1 text-sm text-red-600">{fieldErrors.password}</p>
          )}
        </div>

        <div>
          <label htmlFor="password_confirm" className="block text-sm font-medium text-gray-700">
            パスワード確認
          </label>
          <input
            id="password_confirm"
            name="password_confirm"
            type="password"
            autoComplete="new-password"
            value={formData.password_confirm}
            onChange={handleUserInfoChange}
            className={
              'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-black focus:border-black' +
              inputErrorClass('password_confirm')
            }
            placeholder="パスワードを再入力"
          />
          {fieldErrors.password_confirm && (
            <p className="mt-1 text-sm text-red-600">{fieldErrors.password_confirm}</p>
          )}
        </div>

        <button
          type="submit"
          disabled={isCheckingUserInfo}
          className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-black hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-black cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isCheckingUserInfo ? '確認中...' : '次へ'}
        </button>
      </form>
    </div>
  );

  const renderProfileForm = () => (
    <div className="space-y-6">
      <div className="text-center">
        <button
          onClick={() => setStep('user-info')}
          className="text-sm text-gray-600 hover:text-black cursor-pointer"
        >
          ← 戻る
        </button>
        <h2 className="mt-4 text-3xl font-extrabold text-gray-900">
          {userType === 'contributor' ? '団体情報' : '個人情報'}
        </h2>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        {fieldErrors._form && (
          <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded text-sm">
            {fieldErrors._form}
          </div>
        )}
        {fieldErrors.email && (
          <p className="text-sm text-red-600">
            {fieldErrors.email}（上の「← 戻る」で基本情報のメールを変更できます）
          </p>
        )}

        {userType === 'contributor' ? (
          <>
            <div>
              <label htmlFor="company_name" className="block text-sm font-medium text-gray-700">
                商号 *
              </label>
              <input
                id="company_name"
                name="company_name"
                type="text"
                value={formData.profile.company_name ?? ''}
                onChange={handleProfileChange}
                className={
                  'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-black focus:border-black' +
                  inputErrorClass('company_name')
                }
                placeholder="会社名や自治体名など"
              />
              {fieldErrors.company_name && (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.company_name}</p>
              )}
            </div>

            <div>
              <label htmlFor="representative_name" className="block text-sm font-medium text-gray-700">
                担当者名 *
              </label>
              <input
                id="representative_name"
                name="representative_name"
                type="text"
                value={formData.profile.representative_name ?? ''}
                onChange={handleProfileChange}
                className={
                  'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-black focus:border-black' +
                  inputErrorClass('representative_name')
                }
                placeholder="担当者名"
              />
              {fieldErrors.representative_name && (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.representative_name}</p>
              )}
            </div>

            <div>
              <label htmlFor="industry" className="block text-sm font-medium text-gray-700">
                業種（任意）
              </label>
              <input
                id="industry"
                name="industry"
                type="text"
                value={formData.profile.industry ?? ''}
                onChange={handleProfileChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-black focus:border-black"
                placeholder="業種"
              />
            </div>
          </>
        ) : (
          <>
            <div>
              <label htmlFor="full_name" className="block text-sm font-medium text-gray-700">
                氏名（任意）
              </label>
              <input
                id="full_name"
                name="full_name"
                type="text"
                value={formData.profile.full_name ?? ''}
                onChange={handleProfileChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-black focus:border-black"
                placeholder="氏名"
              />
            </div>

            <div>
              <label htmlFor="gender" className="block text-sm font-medium text-gray-700">
                性別（任意）
              </label>
              <select
                id="gender"
                name="gender"
                value={formData.profile.gender ?? ''}
                onChange={handleProfileChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-black focus:border-black"
              >
                <option value="">選択しない</option>
                <option value="male">男性</option>
                <option value="female">女性</option>
                <option value="other">その他</option>
              </select>
            </div>

            <div>
              <label htmlFor="birth_date" className="block text-sm font-medium text-gray-700">
                生年月日（任意）
              </label>
              <input
                id="birth_date"
                name="birth_date"
                type="date"
                value={formData.profile.birth_date ?? ''}
                onChange={handleProfileChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-black focus:border-black"
              />
            </div>
          </>
        )}

        <div>
          <label htmlFor="address" className="block text-sm font-medium text-gray-700">
            住所 {userType === 'contributor' ? '*' : '（任意）'}
          </label>
          <textarea
            id="address"
            name="address"
            rows={3}
            value={formData.profile.address}
            onChange={handleProfileChange}
            className={
              'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-black focus:border-black' +
              inputErrorClass('address')
            }
            placeholder="住所"
          />
          {fieldErrors.address && (
            <p className="mt-1 text-sm text-red-600">{fieldErrors.address}</p>
          )}
        </div>

        <div>
          <label htmlFor="phone_number" className="block text-sm font-medium text-gray-700">
            電話番号 {userType === 'contributor' ? '*' : '（任意）'}
          </label>
          <input
            id="phone_number"
            name="phone_number"
            type="tel"
            value={formData.profile.phone_number}
            onChange={handleProfileChange}
            className={
              'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-black focus:border-black' +
              inputErrorClass('phone_number')
            }
            placeholder="電話番号"
          />
          {fieldErrors.phone_number && (
            <p className="mt-1 text-sm text-red-600">{fieldErrors.phone_number}</p>
          )}
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={isLoading}
          className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-black hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-black cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? '登録中...' : '登録完了'}
        </button>
      </form>
    </div>
  );

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* 戻るボタン */}
        <div className="text-left">
          <Link
            href="/"
            className="inline-flex items-center text-sm text-gray-600 hover:text-black transition-colors"
          >
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            ホームに戻る
          </Link>
        </div>

        {step === 'user-type' && renderUserTypeSelection()}
        {step === 'user-info' && renderUserInfoForm()}
        {step === 'profile' && renderProfileForm()}

        <div className="text-center">
          <span className="text-sm text-gray-600">
            すでにアカウントをお持ちの方は{' '}
            <Link href="/auth/login" className="font-medium text-black hover:underline">
              ログイン
            </Link>
          </span>
        </div>
      </div>
    </div>
  );
}
