/**
 * 課題詳細ページ
 * 課題の詳細情報を表示
 */
'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import type { Challenge } from '../../../types/challenge';
import { getChallenge } from '../../../lib/challengeAPI';
import { useAuth } from '../../../contexts/AuthContext';

const ChallengeDetailPage: React.FC = () => {
  const params = useParams();
  const router = useRouter();
  const { user, isAuthenticated } = useAuth();
  const [challenge, setChallenge] = useState<Challenge | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const challengeId = params.id as string;

  // 課題詳細の取得
  const fetchChallenge = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const challengeData = await getChallenge(parseInt(challengeId));
      setChallenge(challengeData);
    } catch (err) {
      setError(err instanceof Error ? err.message : '課題の取得に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (challengeId) {
      fetchChallenge();
    }
  }, [challengeId]);

  // 期限の表示形式
  const formatDeadline = (deadline: string) => {
    const date = new Date(deadline);
    return date.toLocaleDateString('ja-JP', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      weekday: 'long'
    });
  };

  // 報酬の表示形式
  const formatReward = (amount: number) => {
    return `¥${amount.toLocaleString()}`;
  };

  // ステータスに応じた表示色とラベル
  const getStatusDisplay = (status: string) => {
    switch (status) {
      case 'open':
        return { label: '募集中', color: 'text-green-600 bg-green-100' };
      case 'closed':
        return { label: '締切', color: 'text-red-600 bg-red-100' };
      case 'completed':
        return { label: '完了', color: 'text-blue-600 bg-blue-100' };
      default:
        return { label: status, color: 'text-gray-600 bg-gray-100' };
    }
  };

  // ローディング表示
  if (loading) {
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

  const statusDisplay = getStatusDisplay(challenge.status);

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* ナビゲーション */}
        <div className="mb-6">
          <Link
            href="/challenges"
            className="text-gray-600 hover:text-gray-800 transition-colors duration-200"
          >
            ← 課題一覧に戻る
          </Link>
        </div>

        {/* 課題ヘッダー */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <div className="flex justify-between items-start mb-4">
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                {challenge.title}
              </h1>
              <div className="flex items-center gap-4 text-sm text-gray-600">
                <span>投稿者: {challenge.contributor_info?.username || '不明'}</span>
                <span>投稿日: {new Date(challenge.created_at).toLocaleDateString('ja-JP')}</span>
              </div>
            </div>
            <span className={`px-3 py-1 text-sm font-medium rounded-full ${statusDisplay.color}`}>
              {statusDisplay.label}
            </span>
          </div>

          {/* 報酬情報 */}
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-500 mb-1">提案報酬</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatReward(challenge.reward_amount)}
              </p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-500 mb-1">採用報酬</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatReward(challenge.adoption_reward)}
              </p>
            </div>
          </div>

          {/* 選出人数と期限 */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-blue-50 rounded-lg p-4">
              <p className="text-sm text-blue-600 mb-1">選出人数</p>
              <p className="text-xl font-semibold text-blue-900">
                {challenge.required_participants}人
              </p>
            </div>
            <div className="bg-orange-50 rounded-lg p-4">
              <p className="text-sm text-orange-600 mb-1">期限</p>
              <p className="text-lg font-semibold text-orange-900">
                {formatDeadline(challenge.deadline)}
              </p>
            </div>
          </div>
        </div>

        {/* 課題内容 */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">課題内容</h2>
          <div className="prose max-w-none">
            <p className="text-gray-700 whitespace-pre-wrap">
              {challenge.description}
            </p>
          </div>
        </div>

        {/* アクションボタン */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex gap-4">
            {/* 投稿者の場合 */}
            {user?.user_type === 'contributor' && user.id === challenge.contributor && (
              <>
                <Link
                  href={`/challenges/${challenge.id}/edit`}
                  className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors duration-200"
                >
                  課題を編集
                </Link>
                <button
                  onClick={() => {
                    if (confirm('この課題を削除しますか？')) {
                      // TODO: 削除処理
                      console.log('削除処理:', challenge.id);
                    }
                  }}
                  className="bg-red-600 text-white px-6 py-2 rounded-lg hover:bg-red-700 transition-colors duration-200"
                >
                  課題を削除
                </button>
              </>
            )}

            {/* 提案者の場合 */}
            {user?.user_type === 'proposer' && challenge.status === 'open' && (
              <Link
                href={`/challenges/${challenge.id}/propose`}
                className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-colors duration-200"
              >
                解決案を提案
              </Link>
            )}

            {/* 未認証ユーザー */}
            {!isAuthenticated && (
              <Link
                href="/auth/login"
                className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors duration-200"
              >
                ログインして参加
              </Link>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChallengeDetailPage;
