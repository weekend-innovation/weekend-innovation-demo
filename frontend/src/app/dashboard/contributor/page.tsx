/**
 * 投稿者用ダッシュボードページ
 * 投稿者が課題と提案の状況を確認できる画面
 */
'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import type { ChallengeListItem } from '../../../types/challenge';
import type { ProposalListItem } from '../../../types/proposal';
import { getChallenges } from '../../../lib/challengeAPI';
import { getProposals } from '../../../lib/proposalAPI';
import { useAuth } from '../../../contexts/AuthContext';

const ContributorDashboard: React.FC = () => {
  const { user } = useAuth();
  const [challenges, setChallenges] = useState<ChallengeListItem[]>([]);
  const [proposals, setProposals] = useState<ProposalListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // ダッシュボードデータの取得
  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // 課題データの取得
      const challengesResponse = await getChallenges();
      setChallenges(challengesResponse.results || []);
      
      // 提案データの取得
      const proposalsResponse = await getProposals();
      setProposals(proposalsResponse.results || []);
      
    } catch (err) {
      console.error('Dashboard data fetch error:', err);
      setError(err instanceof Error ? err.message : 'データの取得に失敗しました');
      // エラー時は空配列を設定
      setChallenges([]);
      setProposals([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  // 統計情報の計算（安全な処理）
  const totalChallenges = challenges?.length || 0;
  const openChallenges = challenges?.filter(c => c.status === 'open').length || 0;
  const totalProposals = proposals?.length || 0;
  const adoptedProposals = proposals?.filter(p => p.is_adopted).length || 0;

  // 最近の課題（最新5件）
  const recentChallenges = challenges?.slice(0, 5) || [];
  
  // 最近の提案（最新5件）
  const recentProposals = proposals?.slice(0, 5) || [];

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
              onClick={fetchDashboardData}
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
          <div className="flex justify-between items-center">
            <h1 className="text-3xl font-bold text-gray-900">ダッシュボード</h1>
            <Link
              href="/challenges/create"
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors duration-200"
            >
              新しい課題を投稿
            </Link>
          </div>
        </div>

        {/* 統計カード */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                  <span className="text-blue-600 text-sm font-medium">📝</span>
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">総課題数</p>
                <p className="text-2xl font-semibold text-gray-900">{totalChallenges}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                  <span className="text-green-600 text-sm font-medium">🟢</span>
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">募集中</p>
                <p className="text-2xl font-semibold text-gray-900">{openChallenges}</p>
              </div>
            </div>
          </div>

        </div>


        <div className="space-y-8">
          {/* 最近の課題 */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-gray-900">最近の課題</h2>
              <Link
                href="/challenges"
                className="text-blue-600 hover:text-blue-800 text-sm font-medium"
              >
                すべて見る
              </Link>
            </div>
            {recentChallenges.length === 0 ? (
              <p className="text-gray-500 text-center py-4">まだ課題を投稿していません</p>
            ) : (
              <div className="space-y-3">
                {recentChallenges.map((challenge) => (
                  <div key={challenge.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">{challenge.title}</p>
                      <p className="text-xs text-gray-500">
                        {new Date(challenge.created_at).toLocaleDateString('ja-JP')} • 
                        {challenge.status === 'open' ? '募集中' : challenge.status === 'closed' ? '締切' : '完了'}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-500">
                        ¥{challenge.reward_amount.toLocaleString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 最近の提案 */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-gray-900">最近の提案</h2>
              <Link
                href="/proposals"
                className="text-blue-600 hover:text-blue-800 text-sm font-medium"
              >
                すべて見る
              </Link>
            </div>
            {recentProposals.length === 0 ? (
              <p className="text-gray-500 text-center py-4">まだ提案がありません</p>
            ) : (
              <div className="space-y-3">
                {recentProposals.map((proposal) => (
                  <div key={proposal.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">{proposal.challenge_title}</p>
                      <p className="text-xs text-gray-500">
                        {proposal.proposer_name} • {new Date(proposal.created_at).toLocaleDateString('ja-JP')}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      {proposal.is_adopted && (
                        <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">
                          採用済み
                        </span>
                      )}
                      <span className="text-xs text-gray-500">
                        {proposal.evaluation_count}評価
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ContributorDashboard;
