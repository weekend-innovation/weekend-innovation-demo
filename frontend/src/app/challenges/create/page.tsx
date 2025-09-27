/**
 * 課題作成ページ
 * 投稿者のみアクセス可能
 */
'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import ChallengeForm from '../../../components/challenges/ChallengeForm';
import type { CreateChallengeRequest } from '../../../types/challenge';
import { createChallenge } from '../../../lib/challengeAPI';
import { useAuth } from '../../../contexts/AuthContext';

const CreateChallengePage: React.FC = () => {
  const router = useRouter();
  const { user, isAuthenticated } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 認証チェック
  if (!isAuthenticated || user?.user_type !== 'contributor') {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <h2 className="text-lg font-medium text-yellow-800 mb-2">
              アクセス権限がありません
            </h2>
            <p className="text-yellow-700 mb-4">
              課題の投稿は投稿者アカウントでのみ可能です。
            </p>
            <Link
              href="/auth/login"
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors duration-200"
            >
              ログイン
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // 課題作成処理
  const handleSubmit = async (data: CreateChallengeRequest) => {
    try {
      setIsLoading(true);
      setError(null);

      const newChallenge = await createChallenge(data);
      
      // 作成成功時は課題詳細ページに遷移
      router.push(`/challenges/${newChallenge.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : '課題の作成に失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* ヘッダー */}
        <div className="mb-8">
          <div className="flex items-center gap-4 mb-4">
            <Link
              href="/dashboard/contributor"
              className="text-gray-600 hover:text-gray-800 transition-colors duration-200"
            >
              ← 戻る
            </Link>
          </div>
          <h1 className="text-3xl font-bold text-gray-900">新しい課題を投稿</h1>
          <p className="mt-2 text-gray-600">
            解決したい課題を投稿して、提案者からの解決案を募集しましょう。
          </p>
        </div>

        {/* エラー表示 */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="text-red-800">{error}</div>
          </div>
        )}

        {/* 課題作成フォーム */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <ChallengeForm
            onSubmit={handleSubmit}
            isLoading={isLoading}
            mode="create"
          />
        </div>

      </div>
    </div>
  );
};

export default CreateChallengePage;
