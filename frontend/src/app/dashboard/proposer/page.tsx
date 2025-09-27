/**
 * 提案者用ダッシュボードページ
 * 提案者が提案活動の状況を確認できる画面
 */
'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import type { ProposalListItem } from '../../../types/proposal';
import type { ChallengeListItem } from '../../../types/challenge';
import { getProposals } from '../../../lib/proposalAPI';
import { getChallenges } from '../../../lib/challengeAPI';
import { useAuth } from '../../../contexts/AuthContext';

const ProposerDashboard: React.FC = () => {
  const { user } = useAuth();
  const [proposals, setProposals] = useState<ProposalListItem[]>([]);
  const [challenges, setChallenges] = useState<ChallengeListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // ダッシュボードデータの取得
  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // 提案データの取得
      const proposalsResponse = await getProposals();
      console.log('Proposals response:', proposalsResponse);
      setProposals(proposalsResponse.results || []);
      
      // 課題データの取得（募集中の課題）
      const challengesResponse = await getChallenges();
      console.log('Challenges response:', challengesResponse);
      setChallenges(challengesResponse.results || []);
      
    } catch (err) {
      console.error('Dashboard data fetch error:', err);
      setError(err instanceof Error ? err.message : 'データの取得に失敗しました');
      // エラー時は空配列を設定
      setProposals([]);
      setChallenges([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  // 統計情報の計算（安全な処理）
  const totalProposals = proposals?.length || 0;
  const adoptedProposals = proposals?.filter(p => p.is_adopted).length || 0;
  const totalEvaluations = proposals?.reduce((sum, p) => sum + (p.evaluation_count || 0), 0) || 0;
  const averageEvaluation = totalProposals > 0 ? Math.round((totalEvaluations / totalProposals) * 10) / 10 : 0;

  // 最近の提案（最新5件）
  const recentProposals = proposals?.slice(0, 5) || [];
  
  // 評価の多い提案（上位5件）
  const topEvaluatedProposals = proposals
    ?.sort((a, b) => (b.evaluation_count || 0) - (a.evaluation_count || 0))
    .slice(0, 5) || [];

  // 募集中の課題（最新5件）
  const openChallenges = challenges?.filter(c => c.status === 'open').slice(0, 5) || [];

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
              href="/challenges"
              className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-colors duration-200"
            >
              新しい提案を投稿
            </Link>
          </div>
        </div>

        {/* 統計カード */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                  <span className="text-blue-600 text-sm font-medium">💡</span>
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">総提案数</p>
                <p className="text-2xl font-semibold text-gray-900">{totalProposals}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                  <span className="text-green-600 text-sm font-medium">✅</span>
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">採用数</p>
                <p className="text-2xl font-semibold text-gray-900">{adoptedProposals}</p>
              </div>
            </div>
          </div>

        </div>


        <div className="space-y-8">
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
              <p className="text-gray-500 text-center py-4">まだ提案を投稿していません</p>
            ) : (
              <div className="space-y-3">
                {recentProposals.map((proposal) => (
                  <div key={proposal.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">{proposal.challenge_title}</p>
                      <p className="text-xs text-gray-500">
                        {new Date(proposal.created_at).toLocaleDateString('ja-JP')}
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

        {/* 募集中の課題 */}
        <div className="mt-8 bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-gray-900">募集中の課題</h2>
            <Link
              href="/challenges"
              className="text-blue-600 hover:text-blue-800 text-sm font-medium"
            >
              すべて見る
            </Link>
          </div>
          {openChallenges.length === 0 ? (
            <p className="text-gray-500 text-center py-4">現在、募集中の課題はありません</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {openChallenges.map((challenge) => (
                <div key={challenge.id} className="p-4 bg-gray-50 rounded-lg">
                  <h3 className="text-sm font-medium text-gray-900 mb-2">{challenge.title}</h3>
                  <div className="flex justify-between items-center text-xs text-gray-500">
                    <span>報酬: ¥{challenge.reward_amount.toLocaleString()}</span>
                    <span>期限: {new Date(challenge.deadline).toLocaleDateString('ja-JP')}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProposerDashboard;
