/**
 * 提案一覧ページ
 * ユーザータイプに応じて表示内容を変更
 */
'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import ProposalCard from '@/components/proposals/ProposalCard';
import type { ProposalListItem, ProposalListResponse } from '@/types/proposal';
import { getProposals } from '@/lib/proposalAPI';
import { useAuth } from '@/contexts/AuthContext';

const ProposalsPage: React.FC = () => {
  const { user, isAuthenticated } = useAuth();
  const [proposals, setProposals] = useState<ProposalListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 提案一覧の取得
  const fetchProposals = async () => {
    console.log('fetchProposals called');
    console.log('isAuthenticated:', isAuthenticated);
    console.log('user:', user);
    
    // 認証されていない場合はAPI呼び出しを避ける
    if (!isAuthenticated || !user) {
      console.log('Not authenticated, skipping API calls');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      console.log('Calling getProposals API...');
      const response: ProposalListResponse = await getProposals();
      console.log('Proposals API response:', response);
      console.log('Response type:', typeof response);
      console.log('Response is array:', Array.isArray(response));
      console.log('Response.results:', response.results);
      if (response.results && response.results.length > 0) {
        console.log('First proposal structure:', response.results[0]);
        console.log('First proposal challenge field:', response.results[0].challenge_id);
      }
      
      // レスポンスが配列の場合は直接使用、オブジェクトの場合はresultsプロパティを使用
      let proposalsData: ProposalListItem[] = [];
      if (Array.isArray(response)) {
        proposalsData = response;
        console.log('Using response as array');
      } else if (response && response.results) {
        proposalsData = response.results;
        console.log('Using response.results');
      } else if (response) {
        // 単一のオブジェクトの場合は空配列にする
        proposalsData = [];
        console.log('Single response object, setting empty array');
      }
      
      setProposals(proposalsData);
      console.log('Proposals set:', proposalsData);
    } catch (err) {
      console.error('Error fetching proposals:', err);
      setError(err instanceof Error ? err.message : '提案の取得に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated && user) {
      fetchProposals();
    } else if (!isAuthenticated) {
      setLoading(false);
    }
  }, [isAuthenticated, user]);


  // 提案編集処理（提案者のみ）
  const handleProposalEdit = (proposal: ProposalListItem) => {
    if (user?.user_type === 'proposer') {
      window.location.href = `/proposals/${proposal.id}/edit`;
    }
  };

  // 提案削除処理（提案者のみ）
  const handleProposalDelete = async (proposal: ProposalListItem) => {
    if (user?.user_type === 'proposer' && confirm('この提案を削除しますか？')) {
      // TODO: 削除API呼び出し
      console.log('削除処理:', proposal.id);
    }
  };

  // 提案採用処理（投稿者のみ）
  const handleProposalAdopt = async (proposal: ProposalListItem) => {
    if (user?.user_type === 'contributor' && confirm('この提案を採用しますか？')) {
      // TODO: 採用API呼び出し
      console.log('採用処理:', proposal.id);
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
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* ヘッダー */}
        <div className="mb-8">
          {/* パンくずリスト */}
          <nav className="flex items-center space-x-2 text-sm text-gray-500 mb-4">
            <Link href="/dashboard" className="hover:text-gray-700">
              ダッシュボード
            </Link>
            <span>/</span>
            <span className="text-gray-900 font-medium">解決案一覧</span>
          </nav>
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
            
            {/* 提案者のみ提案作成ボタンを表示 */}
            {user?.user_type === 'proposer' && (
              <Link
                href="/challenges"
                className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-colors duration-200"
              >
                新しい解決案を提案
              </Link>
            )}
          </div>
        </div>

        {/* 提案一覧 */}
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
