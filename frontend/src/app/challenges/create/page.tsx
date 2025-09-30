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
  const { user, isAuthenticated, token } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

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
      setSuccessMessage(null);

      console.log('課題作成開始:', data);
      const newChallenge = await createChallenge(data);
      console.log('課題作成成功:', newChallenge);
      
      // 選出機能を実行（失敗しても課題投稿は成功とする）
      try {
        console.log('選出機能開始');
        const selectionResponse = await fetch(`http://localhost:8000/api/selections/execute/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
             'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            challenge_id: newChallenge.id,
            required_count: newChallenge.required_participants,
            selection_method: 'random',
            selection_criteria: {}
          })
        });
        
        if (selectionResponse.ok) {
          const selectionResult = await selectionResponse.json();
          console.log('選出完了:', selectionResult);
          setSuccessMessage('課題が正常に投稿され、提案者の選出が完了しました！');
        } else {
          const errorText = await selectionResponse.text();
          console.error('選出エラー:', errorText);
          setSuccessMessage('課題が正常に投稿されました！（選出機能は後で実行されます）');
        }
      } catch (selectionError) {
        console.error('選出機能エラー:', selectionError);
        setSuccessMessage('課題が正常に投稿されました！（選出機能は後で実行されます）');
      }
      
      // 2秒後に課題一覧ページに遷移
      setTimeout(() => {
        router.push('/challenges');
      }, 2000);
      
    } catch (err) {
      console.error('課題作成エラー:', err);
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
          {/* パンくずリスト */}
          <nav className="flex items-center space-x-2 text-sm text-gray-500 mb-4">
            <Link href="/dashboard" className="hover:text-gray-700">
              ダッシュボード
            </Link>
            <span>/</span>
            <span className="text-gray-900 font-medium">新しい課題を投稿</span>
          </nav>
          
          <h1 className="text-3xl font-bold text-gray-900">新しい課題を投稿</h1>
          <p className="mt-2 text-gray-600">
            解決したい課題を投稿して、提案者からの解決案を募集しましょう。
          </p>
        </div>

        {/* 成功メッセージ表示 */}
        {successMessage && (
          <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="text-green-800">{successMessage}</div>
            <div className="text-green-600 text-sm mt-1">課題一覧ページに移動します...</div>
          </div>
        )}

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
