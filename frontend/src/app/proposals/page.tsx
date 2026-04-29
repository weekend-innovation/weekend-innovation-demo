/**
 * 提案一覧ページ
 * ユーザータイプに応じて表示内容を変更
 */
'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import ProposalCard from '@/components/proposals/ProposalCard';
import type { ProposalListItem, ProposalListResponse } from '@/types/proposal';
import { getProposals } from '@/lib/proposalAPI';
import { useAuth } from '@/contexts/AuthContext';

const ProposalsPage: React.FC = () => {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const [proposals, setProposals] = useState<ProposalListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchProposals = useCallback(async () => {
    if (!isAuthenticated || !user) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response: ProposalListResponse = await getProposals();

      let proposalsData: ProposalListItem[] = [];
      if (Array.isArray(response)) {
        proposalsData = response;
      } else if (response && response.results) {
        proposalsData = response.results;
      } else if (response) {
        proposalsData = [];
      }

      setProposals(proposalsData);
    } catch (err) {
      console.error('Error fetching proposals:', err);
      setError(err instanceof Error ? err.message : '提案の取得に失敗しました');
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated, user]);

  useEffect(() => {
    if (authLoading) return;
    if (isAuthenticated && user) {
      void fetchProposals();
    } else {
      setLoading(false);
    }
  }, [authLoading, isAuthenticated, user, fetchProposals]);

  // 認証チェック
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
              このページを閲覧するにはログインが必要です。
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


  // 提案編集処理（提案者のみ）
  const handleProposalEdit = (proposal: ProposalListItem) => {
    if (user?.user_type === 'proposer') {
      window.location.href = `/proposals/${proposal.id}/edit`;
    }
  };

  // 提案削除処理（提案者のみ）
  const handleProposalDelete = async (proposal: ProposalListItem) => {
    void proposal;
    if (user?.user_type === 'proposer' && confirm('この提案を削除しますか？')) {
      // TODO: 削除API呼び出し
    }
  };

  // 提案採用処理（投稿者のみ）
  const handleProposalAdopt = async (proposal: ProposalListItem) => {
    void proposal;
    if (user?.user_type === 'contributor' && confirm('この提案を採用しますか？')) {
      // TODO: 採用API呼び出し
    }
  };

  // ローディング表示
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8 w-full min-w-0">
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
      <div className="min-h-screen bg-gray-50 py-8 w-full">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="text-red-800">{error}</div>
            <button
              onClick={fetchProposals}
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
    <div className="min-h-screen bg-gray-50 py-8 w-full">
      {/* パンくずリスト */}
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 mb-4">
        <nav className="flex items-center space-x-2 text-sm text-gray-500">
          <Link href="/dashboard" className="hover:text-gray-700">
            ホーム
          </Link>
          <span>/</span>
          <span className="text-gray-900 font-medium">解決案一覧</span>
        </nav>
      </div>

      {/* 提案一覧（中央寄せ・固定幅） */}
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* ページヘッダー */}
        <div className="mb-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                {user?.user_type === 'proposer' ? '提案した解決案' : '解決案一覧'}
              </h1>
              <p className="mt-2 text-gray-600">
                {user?.user_type === 'proposer' 
                  ? 'あなたが提案した解決案の一覧です'
                  : 'あなたの課題に対する解決案の一覧です'
                }
              </p>
            </div>
            
          </div>
        </div>
        {!proposals || proposals.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-gray-500 text-lg mb-4">
              {user?.user_type === 'proposer' 
                ? 'まだ解決案を提案していません'
                : '現在、提案はありません'
              }
            </div>
            {user?.user_type === 'proposer' && (
              <Link
                href="/challenges"
                className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-colors duration-200"
              >
                最初の解決案を提案
              </Link>
            )}
          </div>
        ) : (
          <div className="space-y-6">
            {proposals.map((proposal) => (
                    <ProposalCard
                      key={proposal.id}
                      proposal={proposal}
                      showActions={true}
                      showEditDelete={false}
                      showStatus={false}
                      showComments={true}
                      showChallengeInfo={true}
                      onEdit={user?.user_type === 'proposer' ? handleProposalEdit : undefined}
                      onDelete={user?.user_type === 'proposer' ? handleProposalDelete : undefined}
                      onAdopt={user?.user_type === 'contributor' ? handleProposalAdopt : undefined}
                      onComments={(proposal) => {
                        // 提案リスト内の該当提案の未読コメント数を更新
                        if (proposals) {
                          const updatedProposals = proposals.map(p => 
                            p.id === proposal.id ? { ...p, unread_comment_count: 0 } : p
                          );
                          setProposals(updatedProposals);
                        }
                      }}
                    />
            ))}
          </div>
        )}

        {/* ページネーション（TODO: 実装予定） */}
        {proposals && proposals.length > 0 && (
          <div className="mt-8 flex justify-center">
            <div className="text-gray-600 text-sm">
              表示中: {proposals.length}件
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProposalsPage;
