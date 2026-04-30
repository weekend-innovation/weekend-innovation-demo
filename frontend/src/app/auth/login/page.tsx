/**
 * ログインページ
 * ログイン成功後はユーザータイプに応じてダッシュボードにリダイレクト
 */
'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '../../../contexts/AuthContext';

const LoginPage: React.FC = () => {
  const router = useRouter();
  const { user, isAuthenticated, login, isLoading } = useAuth();
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // 既にログインしている場合はダッシュボードにリダイレクト
  useEffect(() => {
    if (isAuthenticated && user) {
      const dashboardPath = user.user_type === 'contributor' 
        ? '/dashboard/contributor' 
        : '/dashboard/proposer';
      router.push(dashboardPath);
    }
  }, [isAuthenticated, user, router]);

  // フォーム送信処理
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (isSubmitting) return;
    
    try {
      setIsSubmitting(true);
      setError(null);
      
      await login(formData.username, formData.password);
      
      // ログイン成功時はuseEffectでリダイレクトされる
    } catch (err) {
      setError(err instanceof Error ? err.message : 'ログインに失敗しました');
    } finally {
      setIsSubmitting(false);
    }
  };

  // 入力値の変更処理
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // エラーをクリア
    if (error) {
      setError(null);
    }
  };

  // ローディング表示
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-600">読み込み中...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* ヘッダー */}
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            アカウントにログイン
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            または{' '}
            <Link
              href="/auth/register"
              className="font-medium text-blue-600 hover:text-blue-500"
            >
              新しいアカウントを作成
            </Link>
          </p>
        </div>

        {/* ログインフォーム */}
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {/* エラー表示 */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="text-red-800 text-sm">{error}</div>
            </div>
          )}

          <div className="space-y-4">
            {/* ユーザー名 */}
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700">
                ユーザー名
              </label>
              <input
                id="username"
                name="username"
                type="text"
                required
                value={formData.username}
                onChange={handleChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="ユーザー名"
              />
            </div>

            {/* パスワード */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                パスワード
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                value={formData.password}
                onChange={handleChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="パスワード"
              />
            </div>
          </div>

          {/* 送信ボタン */}
          <div>
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? 'ログイン中...' : 'ログイン'}
            </button>
          </div>

          {/* ホームに戻るボタン */}
          <div className="text-center">
            <Link
              href="/"
              className="text-sm text-gray-600 hover:text-gray-800"
            >
              ← ホームに戻る
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
};

export default LoginPage;