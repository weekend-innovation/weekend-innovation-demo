/**
 * 課題一覧ページ
 * ユーザータイプに応じて表示内容を変更
 */
'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import ChallengeCard from '../../components/challenges/ChallengeCard';
import type { ChallengeListItem, ChallengeListResponse } from '../../types/challenge';
import { getChallenges } from '../../lib/challengeAPI';
import { useAuth } from '../../contexts/AuthContext';

const ChallengesPage: React.FC = () => {
  const { user, isAuthenticated } = useAuth();
  const [challenges, setChallenges] = useState<ChallengeListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 課題一覧の取得
  const fetchChallenges = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response: ChallengeListResponse = await getChallenges();
      setChallenges(response.results || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : '課題の取得に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchChallenges();
  }, []);

  // 課題カードのクリック処理
  const handleChallengeView = (challenge: ChallengeListItem) => {
    // 課題詳細ページに遷移
    window.location.href = `/challenges/${challenge.id}`;
  };

  // 課題編集処理（投稿者のみ）
  const handleChallengeEdit = (challenge: ChallengeListItem) => {
    if (user?.user_type === 'contributor') {
      window.location.href = `/challenges/${challenge.id}/edit`;
    }
  };

  // 課題削除処理（投稿者のみ）
  const handleChallengeDelete = async (challenge: ChallengeListItem) => {
    if (user?.user_type === 'contributor' && confirm('この課題を削除しますか？')) {
      // TODO: 削除API呼び出し
      console.log('削除処理:', challenge.id);
    }
  };

  // ローディング表示
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-center items-center h-64">
            <div className="text-gray-600">読み込み中...</div>
          </div>
        </div>
      </div>
    );
  }

  // エラー表示
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="text-red-800">{error}</div>
            <button
              onClick={fetchChallenges}
              className="mt-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors duration-200"
            >
              再試行
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* ヘッダー */}
        <div className="mb-8">
          <div className="flex items-center gap-4 mb-4">
            <Link
              href={user?.user_type === 'contributor' ? '/dashboard/contributor' : '/dashboard/proposer'}
              className="text-gray-600 hover:text-gray-800 transition-colors duration-200"
            >
              ← 戻る
            </Link>
          </div>
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                {user?.user_type === 'contributor' ? '投稿した課題' : '課題一覧'}
              </h1>
              <p className="mt-2 text-gray-600">
                {user?.user_type === 'contributor' 
                  ? 'あなたが投稿した課題の一覧です'
                  : '参加可能な課題の一覧です'
                }
              </p>
            </div>
            
            {/* 投稿者のみ課題作成ボタンを表示 */}
            {user?.user_type === 'contributor' && (
              <Link
                href="/challenges/create"
                className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors duration-200"
              >
                新しい課題を投稿
              </Link>
            )}
          </div>
        </div>

        {/* 課題一覧 */}
        {!challenges || challenges.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-gray-500 text-lg mb-4">
              {user?.user_type === 'contributor' 
                ? 'まだ課題を投稿していません'
                : '現在、参加可能な課題はありません'
              }
            </div>
            {user?.user_type === 'contributor' && (
              <Link
                href="/challenges/create"
                className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors duration-200"
              >
                最初の課題を投稿
              </Link>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {challenges.map((challenge) => (
              <ChallengeCard
                key={challenge.id}
                challenge={challenge}
                showActions={true}
                onView={handleChallengeView}
                onEdit={user?.user_type === 'contributor' ? handleChallengeEdit : undefined}
                onDelete={user?.user_type === 'contributor' ? handleChallengeDelete : undefined}
              />
            ))}
          </div>
        )}

        {/* ページネーション（TODO: 実装予定） */}
        {challenges && challenges.length > 0 && (
          <div className="mt-8 flex justify-center">
            <div className="text-gray-600 text-sm">
              表示中: {challenges.length}件
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChallengesPage;
