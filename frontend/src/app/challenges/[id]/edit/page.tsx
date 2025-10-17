/**
 * 課題編集ページ
 * 投稿者のみアクセス可能
 */
'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import ChallengeForm from '../../../../components/challenges/ChallengeForm';
import type { Challenge, UpdateChallengeRequest } from '../../../../types/challenge';
import { getChallenge, updateChallenge } from '../../../../lib/challengeAPI';
import { useAuth } from '../../../../contexts/AuthContext';

const EditChallengePage: React.FC = () => {
  const params = useParams();
  const router = useRouter();
  const { user, isAuthenticated } = useAuth();
  const [challenge, setChallenge] = useState<Challenge | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isFetching, setIsFetching] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const challengeId = params.id as string;

  // 課題データの取得
  useEffect(() => {
    const fetchChallenge = async () => {
      try {
        setIsFetching(true);
        const challengeData = await getChallenge(parseInt(challengeId));
        setChallenge(challengeData);
      } catch (err) {
        console.error('課題取得エラー:', err);
        setError('課題の取得に失敗しました');
      } finally {
        setIsFetching(false);
      }
    };

    if (isAuthenticated && challengeId) {
      fetchChallenge();
    }
  }, [isAuthenticated, challengeId]);

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
              課題の編集は投稿者アカウントでのみ可能です。
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

  // ローディング表示
  if (isFetching) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-center items-center h-64">
            <div className="text-gray-600">読み込み中...</div>
          </div>
        </div>
      </div>
    );
  }

  // エラー表示
  if (error || !challenge) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <h2 className="text-lg font-medium text-red-800 mb-2">
              エラーが発生しました
            </h2>
            <p className="text-red-700 mb-4">
              {error || '課題が見つかりません'}
            </p>
            <Link
              href="/challenges"
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors duration-200"
            >
              課題一覧に戻る
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // 課題更新処理
  const handleSubmit = async (data: UpdateChallengeRequest) => {
    try {
      setIsLoading(true);
      setError(null);
      setSuccessMessage(null);

      // 編集可能なフィールド（タイトルと内容）のみを送信
      const updateData: UpdateChallengeRequest = {
        title: data.title,
        description: data.description
      };

      console.log('課題更新開始:', updateData);
      const updatedChallenge = await updateChallenge(parseInt(challengeId), updateData);
      console.log('課題更新成功:', updatedChallenge);
      
      setSuccessMessage('課題が正常に更新されました！');
      
      // 2秒後に課題詳細ページに遷移
      setTimeout(() => {
        router.push(`/challenges/${challengeId}`);
      }, 2000);
      
    } catch (err) {
      console.error('課題更新エラー:', err);
      setError(err instanceof Error ? err.message : '課題の更新に失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* ヘッダー */}
        <div className="mb-8">
          {/* パンくずリスト */}
          <nav className="flex items-center space-x-2 text-sm text-gray-500 mb-4">
            <Link href="/dashboard" className="hover:text-gray-700">
              ダッシュボード
            </Link>
            <span>/</span>
            <Link href="/challenges" className="hover:text-gray-700">
              課題一覧
            </Link>
            <span>/</span>
            <Link href={`/challenges/${challengeId}`} className="hover:text-gray-700">
              課題詳細
            </Link>
            <span>/</span>
            <span className="text-gray-900 font-medium">編集</span>
          </nav>
          
          <h1 className="text-3xl font-bold text-gray-900">課題を編集</h1>
          <p className="mt-2 text-gray-600">
            課題の内容を編集できます。
          </p>
        </div>

        {/* 成功メッセージ表示 */}
        {successMessage && (
          <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="text-green-800">{successMessage}</div>
            <div className="text-green-600 text-sm mt-1">課題詳細ページに移動します...</div>
          </div>
        )}

        {/* エラー表示 */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="text-red-800">{error}</div>
          </div>
        )}

        {/* 課題編集フォーム */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <ChallengeForm
            initialData={challenge}
            onSubmit={handleSubmit}
            isLoading={isLoading}
            mode="edit"
          />
        </div>

      </div>
    </div>
  );
};

export default EditChallengePage;

