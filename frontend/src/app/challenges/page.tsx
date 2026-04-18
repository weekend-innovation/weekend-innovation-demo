/**
 * 課題一覧ページ
 * ユーザータイプに応じて表示内容を変更
 */
'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import ChallengeCard from '../../components/challenges/ChallengeCard';
import type { ChallengeListItem } from '../../types/challenge';
import { getAllChallenges, deleteChallenge } from '../../lib/challengeAPI';
import { sortExpiredChallenges, sortActiveContributorChallenges, sortActiveProposerChallenges, isProposerExpiredOrFailed, isContributorExpired } from '../../lib/challengeSortUtils';
import { useAuth } from '../../contexts/AuthContext';

const PAGE_SIZE = 20;

const ChallengesPage: React.FC = () => {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const [challenges, setChallenges] = useState<ChallengeListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);

  // 課題一覧の取得（全件取得してフロントでソート・ページネーション）
  const fetchChallenges = useCallback(async () => {
    if (!isAuthenticated || !user) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const challengesData = await getAllChallenges();
      setChallenges(challengesData);
    } catch (err) {
      console.error('課題一覧取得エラー:', err);
      setError(err instanceof Error ? err.message : '課題の取得に失敗しました');
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated, user]);

  useEffect(() => {
    if (isAuthenticated && user) {
      void fetchChallenges();
    } else if (!isAuthenticated) {
      setLoading(false);
      setError('ログインが必要です');
    }
  }, [isAuthenticated, user, fetchChallenges]);

  useEffect(() => {
    const handleFocus = () => {
      if (isAuthenticated && user) {
        void fetchChallenges();
      }
    };
    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, [isAuthenticated, user, fetchChallenges]);

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
      try {
        await deleteChallenge(challenge.id);
        if (challenges.length <= 1 && currentPage > 1) {
          setCurrentPage((p) => Math.max(1, p - 1));
        }
        fetchChallenges();
      } catch (error) {
        console.error('課題削除エラー:', error);
        alert('課題の削除に失敗しました。');
      }
    }
  };

  // 認証チェック（すべてのHooksの後に配置）
  if (authLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">読み込み中...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50 py-8 w-full min-w-0">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <h2 className="text-lg font-medium text-yellow-800 mb-2">
              ログインが必要です
            </h2>
            <p className="text-yellow-700 mb-4">
              課題一覧を表示するにはログインしてください。
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
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
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
      <div className="min-h-screen bg-gray-50 py-8 w-full min-w-0">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="text-red-800">{error}</div>
            <button
              onClick={() => fetchChallenges()}
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
    <div className="min-h-screen bg-gray-50 py-4 w-full">
      {/* パンくずリスト */}
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 mb-2">
        <nav className="flex items-center space-x-2 text-sm text-gray-500">
          <Link href="/dashboard" className="hover:text-gray-700">
            ホーム
          </Link>
          <span>/</span>
          <span className="text-gray-900 font-medium">
            {user?.user_type === 'contributor' ? '投稿した課題' : '課題一覧'}
          </span>
        </nav>
      </div>

      {/* 課題一覧（中央寄せ・固定幅） */}
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* ページヘッダー（タイトルとカードの間の余白を詰める） */}
        <div className="mb-4">
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
        {(() => {
          // ソート済みリストを算出（従来どおり。ソートを変えない）
          let sortedChallenges: ChallengeListItem[] = [];
          if (challenges && challenges.length > 0) {
            if (user?.user_type === 'proposer') {
              const expiredChallenges = sortExpiredChallenges(
                challenges.filter(c => isProposerExpiredOrFailed(c))
              );
              const activeChallenges = sortActiveProposerChallenges(
                challenges.filter(c => !isProposerExpiredOrFailed(c))
              );
              sortedChallenges = [...activeChallenges, ...expiredChallenges];
            } else {
              const activeChallenges = sortActiveContributorChallenges(
                challenges.filter(c => !isContributorExpired(c))
              );
              const expiredChallenges = sortExpiredChallenges(
                challenges.filter(c => isContributorExpired(c))
              );
              sortedChallenges = [...activeChallenges, ...expiredChallenges];
            }
          }

          const totalCount = sortedChallenges.length;
          const totalPages = Math.ceil(totalCount / PAGE_SIZE) || 1;
          const paginatedChallenges = sortedChallenges.slice(
            (currentPage - 1) * PAGE_SIZE,
            currentPage * PAGE_SIZE
          );

          if (totalCount === 0) {
            return (
              <div className="text-center py-12">
                <div className="text-gray-500 text-lg mb-4">
                  {user?.user_type === 'contributor'
                    ? 'まだ課題を投稿していません'
                    : '現在、参加可能な課題はありません'}
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
            );
          }

          return (
            <>
              <div className="space-y-6 max-w-4xl mx-auto px-8 sm:px-10">
                {paginatedChallenges.map((challenge) => (
                    <ChallengeCard
                      key={challenge.id}
                      challenge={challenge}
                      showActions={true}
                      userType={user?.user_type === 'contributor' ? 'contributor' : 'proposer'}
                      isProposed={user?.user_type === 'proposer' ? !!challenge.has_proposed : undefined}
                      onView={handleChallengeView}
                      onEdit={user?.user_type === 'contributor' ? handleChallengeEdit : undefined}
                      onDelete={user?.user_type === 'contributor' ? handleChallengeDelete : undefined}
                    />
                  ))}
              </div>

              {/* ページネーション（投稿者・提案者共通、1ページ20件） */}
              {totalCount > PAGE_SIZE && (
                <div className="mt-8 flex flex-col items-center gap-4 max-w-4xl mx-auto px-8 sm:px-10">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                      disabled={currentPage <= 1}
                      className="px-4 py-2 rounded-lg border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      前へ
                    </button>
                    <span className="text-sm text-gray-600">
                      {currentPage} / {totalPages} ページ（全 {totalCount} 件）
                    </span>
                    <button
                      onClick={() => setCurrentPage((p) => p + 1)}
                      disabled={currentPage >= totalPages}
                      className="px-4 py-2 rounded-lg border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      次へ
                    </button>
                  </div>
                </div>
              )}
            </>
          );
        })()}
      </div>
    </div>
  );
};

export default ChallengesPage;
